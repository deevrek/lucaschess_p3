//    Copyright 2010 Antonio Torrecillas Gonzalez
//
//    This file is part of Simplex.
//
//    Simplex is free software: you can redistribute it and/or modify
//    it under the terms of the GNU General Public License as published by
//    the Free Software Foundation, either version 3 of the License, or
//    (at your option) any later version.
//
//    Simplex is distributed in the hope that it will be useful,
//    but WITHOUT ANY WARRANTY; without even the implied warranty of
//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//    GNU General Public License for more details.
//
//    You should have received a copy of the GNU General Public License
//    along with Simplex.  If not, see <http://www.gnu.org/licenses/>
//

#ifndef WIN32
#define THREAD
#endif

#include "stdio.h"
#include "stdlib.h"
#include "memory.h"
#include "string.h"
#include <time.h>
#include <assert.h>

// Clase para al base de nuestro programa
#include "Ajedrez.h"

const int DepthReds = 2;
const int SafeLegalRed = 4; 


extern void Print(const char *fmt, ...);

extern u64 ataque[8][64]; // casilla pieza // distinguiendo peones blancos y negros

#include "Sort.h"

#define NMRED 4
const int DepthCache = 1; //3;


u64 PosPartida[512];
int NumMoves;


void CPartida::Nueva()
{

	T.ColorJuegan = 0;
	T.LoadEPD("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - bm 1;id 1;",0);
	T.CalculaJugadasPosibles();
	AnalisisFinalizado = 1;
	PosPartida[0] = T.GetHash();
	NumMoves = 0;
	cancelado = 1;

}

HRESULT CPartida::Mueve(char *Jugada)
{
	int retorno;
	T.CalculaJugadasPosibles();
	if(
		strcmp(Jugada,"0-0") == 0 || 
		strcmp(Jugada,"O-O") == 0 || 
		strcmp(Jugada,"00") == 0 || 
		strcmp(Jugada,"OO") == 0 
		)
	{
		if(T.ColorJuegan == blanco)
		{
			retorno =  T.MueveAlgebra("e1g1");
		}
		else
		{
			retorno =  T.MueveAlgebra("e8g8");
		}
	}
	else if(
		strcmp(Jugada,"0-0-0") == 0 || 
		strcmp(Jugada,"O-O-O") == 0 || 
		strcmp(Jugada,"000") == 0 || 
		strcmp(Jugada,"OOO") == 0 
		)
	{
		if(T.ColorJuegan == blanco)
		{
			retorno =  T.MueveAlgebra("e1c1");
		}
		else
		{
			retorno =  T.MueveAlgebra("e8c8");
		}
	}
	else
	{
		retorno =  T.MueveAlgebra(Jugada);
	}
	NumMoves++;
	T.hash = 0ull;
	PosPartida[NumMoves] = T.GetHash();;
	return retorno;
}

void CPartida::Analiza()
{
	// lanzar un thread que genere una jugada
	// para controlar cuando ha finalizado o debe hacerlo
	// no ha terminado el anterior
	if(AnalisisFinalizado == 0) return;

	AnalisisFinalizado = 0;
	LanzaAnalisis(this);
}


void CPartida::CloseThread()
{
	CierraThreads();
}


CPartida::CPartida()
{
	HashJ.Inicializa();
	InitBranchFactorMesure();
#ifdef _DEBUG
	tiempo_limite = 20000;
#else
	tiempo_limite = 500000;
#endif
}

CPartida::~CPartida()
{
#ifdef THREADS
	if(hThread)
		CloseThread();
#endif
}


#define CORTA

void CPartida::LoadEPD(char *fen)
{
	T.LoadEPD(fen,0);
	PosPartida[0] = T.GetHash();
	NumMoves = 0;
}



void CPartida::Cancela()
{
	cancelado = 1;
}

void CPartida::PrintInfo(int value,char * path)
{
	extern void Print(const char *fmt, ...);

	int time;
	int segs;
	int mate;
	int nps = 0;
//	if(!LimiteProfundidad)
		if(Depth < 3)
			return;

	time = TiempoTranscurrido() - inicio;
	if(time == 0)
		time++;
	segs = time / 1000;
	if(segs == 0)
		segs++;
	if(NodosVisitados < 2000000)
		nps = NodosVisitados*1000/time;
	else
		nps = NodosVisitados / segs;

	mate = 0;
	if(value >= MATE -50)
	{
		mate = MATE -value;
	}
	if(value <= -MATE +50)
	{
		mate = MATE +value;
		mate = -mate;
	}
	if(!mate)
	{
		Print("info depth %d seldepth %d pv %s score cp %d nodes %d nps %d hashfull %d time %ld\n",
			Depth,
			SelDepth,
			path,
			value,
			NodosVisitados,
			nps,
			0,	// numero de veces que se recalcula
			time);
	}
	else
	{
		Print("info depth %d seldepth %d pv %s score mate %d nodes %d nps %d hashfull %d time %ld\n",
			Depth,
			SelDepth,
			path,
			mate/2,
			NodosVisitados,
			nps,
			0,	
			time);
	}
}

u64 BFNodeCount[60];
int BFHitCount[60];

void CPartida::InitBranchFactorMesure()
{
	int i;
	for(i=0;i < 60;i++)
	{
		BFNodeCount[i] = 0ull;
		BFHitCount[i] = 0;
	}
}

void CPartida::DumpBranchFactor()
{
	int i;
	double BF;
	for(i=0;i < 59;i++)
	{
		if(BFNodeCount[i+1] && BFNodeCount[i] )
		{
			BF = ((BFNodeCount[i+1] *1.0)/BFHitCount[i+1]) / ((BFNodeCount[i]*1.0)/BFHitCount[i]);
			printf("BF[%d] = %lf\n",i,BF);
		}
	}
}

void CPartida::IterativeDeepening(void)
{
	extern void Print(const char *fmt, ...);
	long ini_it;
	int value,value_i;
	int hasp;
	int MateCount = 0;
	// busqueda con ventana
	int VAlpha,VBeta,Pase;

	int Valor_d1;
	char JugD1[20];

	ValueSearch = 0;
	NodosVisitados = 0;
	cancelado  = 0;
	NodosRepasados = 0;
	SelDepth = 0;
	inicio = TiempoTranscurrido();

	// copiamos tablero principal
	Taux.LoadEPD(T.SaveEPD(),0);

	ResetHistory();
	char PV[1024];
	PV[0] = '\0';
	value = -INFINITO;
	T.CalculaJugadasPosibles();
	HashJ.IncrementaEdad();
	JugadaActual[0] = '\0';
	strcpy(JugadaActual,T.JugadasPosibles[0].ToString());
	Depth = 1;
	value_i = value = PVS(Depth,-INFINITO,+INFINITO,PV,false);
	Valor_d1 = value_i ;
	if(Valor_d1 == INFINITO || Valor_d1 == -INFINITO)
		Valor_d1 = 0;
	JugD1[0] = '\0';

	if(PV[0])
	{
		strcpy(MejorPath,PV);
		PrintInfo(value,PV);
		strcpy(JugadaActual,strtok(PV," "));
		strcpy(JugD1,JugadaActual);
	}
	BFNodeCount[Depth] += NodosVisitados;
	BFHitCount[Depth]++;
	Depth++;
	VAlpha = value-128;
	VBeta = value+128;
	Pase = 0;
	if(Unica)
	{
		PrintInfo(value,PV);
		strcpy(JugadaActual,strtok(PV," u"));
		Print("bestmove %s\n",JugadaActual);
		return;
	}
	while(1)
	{
		if(cancelado)
			break;
		if(tiempo_limite)
		{
			ini_it = TiempoTranscurrido();
			if((ini_it  - inicio) > tiempo_limite) // tiempo excedido
			{
				break;
			}
		}

		if(LimiteProfundidad)
			if(Depth > LimiteProfundidad)
			{
				if(LimiteProfundidad == 1)
					PrintInfo(value,PV);
				break;
			}
		if(Depth > MAXDEPTHC)
			break;

		SelDepth = 0;
		if(Depth > 2)
			Print("info depth %d \n",Depth);
		hasp = value;
		ResetHistory();
		// nos colocamos en la historia
		// preparamos la primera evaluacion
		Taux.CalculaJugadasPosibles();


		value = PVS(Depth,-INFINITO,+INFINITO,PV,false);
		if( cancelado == 1)
			break;

		PrintInfo(value,PV); // end of iteration-> get time to depth
		BFNodeCount[Depth] += NodosVisitados;
		BFHitCount[Depth]++;

		if(value == MATE || value == -MATE)
		{
			strcpy(JugadaActual,"resign");
			break;
		}
		PV[0] = '\0'; // reset de la mejor jugada
		// llevamos la cuenta de iteraciones que damos o recibimos mate
		if(value < (50-MATE) && value > -MATE)
			MateCount++;
		if(value > (MATE-50) && value < MATE)
			MateCount++;

		// a partir de 5 iteraciones de mate podemos dar el resultado por bueno
		if(tiempo_limite)
		if(MateCount >= 5)
			break;

		Depth++;
	}
	// hemos terminado de pensar
	if(JugadaActual[0])
	{
		for(int i=0;JugadaActual[i];i++)
			if(JugadaActual[i] == '#')
				JugadaActual[i] = '\0';

		if(LimiteProfundidad != 1)
			Print("bestmove %s\n",JugadaActual);
	}
	else
	{
		// no tenemos JugadaActual
		Print("bestmove %s\n",T.JugadasPosibles[0].ToString());
	}
	ValueSearch = value;
}

void CPartida::SetMejorPath(char *path)
{
	char *token;
	CJugada *j;
	char mp[1024];
	strcpy(MejorPath,path);
	strcpy(mp,path);
	// transformar el path  de jugadas
	token = strtok( mp, " " );
	DepthHistoria = 0;
	while( token != NULL )
	{
		/* Trocear cada jugada individual */
		j = &Historia[DepthHistoria];
		j->desglose.f = ((token[1] -'1')<<3) + ((token[0] -'a')& 7);
		j->desglose.t = ((token[3] -'1')<<3) + ((token[2] -'a')& 7);
		if(token[4] != '\0')
		{
			switch(token[4])
			{
			case 'q':
				j->desglose.coronar = dama;
				break;
			case 'r':
				j->desglose.coronar = torre;
				break;
			case 'b':
				j->desglose.coronar = alfil;
				break;
			case 'n':
				j->desglose.coronar = caballo;
				break;
			}
		}
#ifdef _DEBUGA
		// si reconvertimos a cadena debemos recuperar el token
		if(strcmp(token,j->ToString()) != 0)
		{
			// error de conversion
			Print("Error\n");
		}
#endif
		/* Get next token: */
		token = strtok( NULL," " );
		DepthHistoria++;
	}
}
int CPartida::ColorJuegan()
{
	return T.ColorJuegan;
}

int CPartida::HayRepeticion(u64 hash)
// verifica si esta posicion ya la hemos visto
{
	int i;
	int repe = 0;
	for(i=0;i < stHistory;i++)
	{
		if(HashHistory[i] == hash)
			repe++;
	}
	if(repe)
		return repe;
	// buscamos en las posiciones 
	for(i= 0; i < 	NumMoves;i++)
	{
		if(PosPartida[i] == hash)
			repe++;
	}
	if(repe >= 1)
		return 1;
	return 0;
}
void CPartida::SetHashHistory(u64 hash)
// asigna una firma de la posicion
{
	if(cancelado)
		return;
#ifdef _DEBUG
	if(stHistory >= 47 )
		stHistory = stHistory;
#endif

	if(stHistory < MAXDEPTH )
		HashHistory[stHistory++] = hash;
	else
		stHistory--;
	if(stHistory > SelDepth)
		SelDepth = stHistory;
	// salvamos el estado
	StateHistory[stHistory] = Taux.en_pasant + Taux.EstadoEnroque * 64;
}
void CPartida::ResetHistory()
{
	memset(HashHistory,0,sizeof(HashHistory));
	stHistory = 0;
}
void CPartida::PopHistory()
{
	stHistory--;
	if(stHistory < 0)
		stHistory = 0;
}

void CPartida::Move(CJugada &J)
{
	// hacemos el movimiento
	Taux.Mueve(J);
	// guardamos en el stack
	MoveHistory[stHistory] = J;
}
void CPartida::TakeBack()
{
	// deshacemos el movimiento
	Taux.DesMueve(MoveHistory[stHistory]);
	// restauramos el estado
	Taux.EstadoEnroque = StateHistory[stHistory] / 64; 
	Taux.en_pasant = StateHistory[stHistory] % 64;
}

int CPartida::IsRecap(int pos)
{
	if(MoveHistory[stHistory].desglose.t == pos && MoveHistory[stHistory].desglose.captura != ninguna)
	{
		return 1;
	}
	return 0;
}
int CPartida::ValorMate(int signo)
{
	if(signo > 0)
		return( MATE - stHistory);
	else
		return ( -MATE + stHistory);
}
void CPartida::GotoPath(char *path,int depth)
{
	char string[2024];
	char seps[]   = " #,\t\n";
	char *token;
	int i = 0;

	strcpy(string,path);
   /* Establish string and get the first token: */
   token = strtok( string, seps );
   path[0] = '\0';
   while( token != NULL  && i < depth)
   {
	   Taux.tope = 0;
	   Taux.CalculaJugadasPosibles();
	   Taux.MueveAlgebra(token);
	   strcat(path,token);
	   strcat(path," ");
      /* Get next token: */
      token = strtok( NULL, seps );
	  i++;
   }
}

#define FASE_SALIDA 2
#define FASE_CAPTURAS 0
#define FASE_RESTO 1 

//
// Rutina de busqueda principal
//
const int DoDistancePruning = true;
const int UseCache = true;

const int UseNullMove = true;


void CPartida::IncNodes()
{
	// incrementamos los nodos vistos
	NodosVisitados++;
	if(NodosVisitados-NodosRepasados > TOPENODOSREPASO)
	{		
		if(tiempo_limite)
		{
			if(((TiempoTranscurrido() - inicio) > tiempo_limite))
			{
				Cancela();
			}
			else
				NodosRepasados = NodosVisitados;
		}
	}
}


void CPartida::IncNodesQ()
{
	NodosVisitados++;
	if(tiempo_limite)
	if(NodosVisitados-NodosRepasados > TOPENODOSREPASO)
	{		
		if(((TiempoTranscurrido() - inicio) > tiempo_limite))
		{
			Cancela();
		}
		else
			NodosRepasados = NodosVisitados;
	}

}


// buscamos capturas y jaques y analizamos las posibilidades de escape.
int CPartida::Quiesce(int alpha,int beta)
{
	int value,a;

	
	if(cancelado + (stHistory >> 6)) // si llenamos el pozo lo dejamos en tablas
	{
		return Taux.Evalua();
	}

	IncNodesQ();

	u64 hash = Taux.GetHash();

	int Valor_i;

	Valor_i = Taux.Evalua();
	// Vamos con material de sobra
	if(Valor_i >= beta ) 	{		return Valor_i;	}



	a = alpha;
	if(Valor_i > alpha )		a = Valor_i;
	value = a;	alpha = a;

	SetHashHistory(hash);
	CJugada J;
	int legales = 0;

	CSort Sort;
	Sort.Init(Taux,true);

	for(J = Sort.GetNextQ();J.ToInt();J = Sort.GetNextQ())
	{
		if(cancelado)			break;
		if(J.desglose.captura == rey)
		{
			a = ValorMate(1);
			PopHistory();
			return a;
		}

		if(J.desglose.peso < (PesoCaptura+PesoCapturaBuena))			continue;

		Move(J);
		if(!Taux.EsAtacada(Taux.PosReyes[Taux.ColorJuegan^1],Taux.ColorJuegan^1) )
		{
			legales++;
			value = -Quiesce(-beta, -a);
		}
		TakeBack();
		if(value > a) 
		{
			a = value;
			if(a >= beta ) 
			{
				break;
			}
		}	
	} // for

	PopHistory();
	return ( a );   
}

void CPartida::MuevePath(char *path)
{
	char string[2024];
	char seps[]   = " #,\t\n";
	char *token;
	int i = 0;

	strcpy(string,path);
   /* Establish string and get the first token: */
   token = strtok( string, seps );
   while( token != NULL )
   {
	   Mueve(token);
      /* Get next token: */
      token = strtok( NULL, seps );
	  i++;
   }
}




int CPartida::PVS(int depth, int alpha, int beta,char *Global,int doNull)
{
	int ext_local; 
	u64 hash;
	char PV[1024];
	int value = 0;
	int InPV = beta-alpha > 1;
	int EsJaque,legales = 0;
	int fFoundPv = false;
	int Valor_i = 0;
	IncNodes();
	if(cancelado)
		return alpha;

	if(DoDistancePruning)
	{
		// limite inferior
		value = ValorMate(-1);
		value += 2;
		if(value > alpha)
		{
			alpha = value;
			if(value >= beta)
				return value;
		}
		// limite superior
		value = ValorMate(1);
		value--;
		if(value < beta)
		{
			beta = value;
			if(value <= alpha)
				return value;
		}
	}

	hash = Taux.GetHash();
	if(stHistory > 0 && HayRepeticion(hash) ) // Queremos evitar repeticiones pero no en raiz ya que no jugariamos
	{		return 0;	}
	if(EsJaque = Taux.EstoyEnJaque())
	{	depth++; 	}

	if((depth <= 0 || stHistory > MAXDEPTHC)) // extendiendo jaques agotamos la pila
	{
		NodosVisitados--; // correccion para no contarlos dos veces

		value = Quiesce(alpha,beta);//,Global);
#ifdef _DEBUG
		if(value <= -MATE || value >= MATE)
		{
			value = value;
		}
#endif
		assert(value > -MATE && value < MATE);
		return value;
	}
/*
 ************************************************************
 *   Recuperamos el valor del cache                         *
 *                                                          *
 ************************************************************
 */
	if(UseCache)
	{
		if( depth < (Depth-depth) &&
			!EsJaque && !InPV) // 
		{
			int CV = HashJ.GetValue(hash);
			if(CV)
			{
				value = CV & VALUEMASK; // valor
				if(value > MATE)
				{
					value |= 0xffff0000;
				}
				// verificamos la profundidad en cache
				if((CV >> 20) >= (depth) )
				{
					// el valor en cache significa algo
					if(CV & UBOUND)
					{
						if(CV & LBOUND)		
						{		
							if(value >= beta) return beta;
							if(value <= alpha) return alpha;
							return(value);		
						}
						else
						{
							// solo UBOUND
							if(value <= alpha )		{	
								return alpha;	
							}
							if(value < beta)	beta = value;
						}
					}
					else
					{
						if(value >= beta)	{		
							return beta; 		
						}
						if(value > alpha)	{		alpha = value;		}
					}
				}
			}
		}
	} // UseCache
	if(UseNullMove)
	{
		if( 
			doNull &&
			depth >= 2 &&
			!EsJaque  &&
			!InPV 
			&& Taux.TotalPCtm() > 0
			) 
		{
			int d = depth -NMRED;
			if(d < 0) d = 0;
			Taux.SwitchColor();
			PV[0] = '\0';
			value = -PVS(d, -beta,-beta+1,PV,false);
			Taux.SwitchColor();

			{
				if (value >= beta)
				{
					value = beta;
					CACHEA(hash,beta,depth,LBOUND);
#ifdef _DEBUG
					strcpy(Global," NULLMOVE ");
					strcat(Global,PV);
#endif
					return value;
				}
			}
		}
	} // UseNullMove

	Taux.HashJugada = HashJ.GetJ(hash);
	
	// ahora recorremos las jugadas
	CJugada J;
	CSort Sort;

	SetHashHistory(hash);

	// se tiene que hacer en el mismo nivel stHistory por lo que
	// debe ir tras el set hashHistory ...
	for(int k = 0; k < MAXKILLERS;k++)
		Taux.Killer[k] = HashJ.GetKiller(stHistory,k);

	Sort.Init(Taux,false);


	value = alpha;

	int DoLMR = false;
	if(	!EsJaque && depth > 1	&& Taux.TotalPCtm() > 1
		)
	{
		DoLMR = true;	
	}

	int MejorJ;

	int Mat = 0;
	bool DoFutil = false;
	if(	!EsJaque && depth < 5 
		)
	{
		const int Margin[5] = {0,60,80,200,200};
		Mat = Taux.GetMatValue();
		if((Mat + Margin[depth]) < alpha)
			DoFutil = true;

	}


	MejorJ = 0;	PV[0] = '\0';
	for(J = Sort.GetNext();J.ToInt();J = Sort.GetNext())
	{
		if(cancelado)
			break;
		ext_local = 0;
		if(J.desglose.captura == rey)
		{
			// esta posicion es mate
			alpha = ValorMate(-1);
			if(alpha >=beta)
			{
				CACHEA(hash,beta,depth,LBOUND);
				HashJ.Push(hash,J);
			}
			PopHistory();
            return alpha;
		}

		if(!EsJaque) // ya hemos extendido
		{
			if(	Taux.Es7a(J))
				ext_local = 1;
			if(DoLMR && ext_local == 0  && legales > SafeLegalRed) 
			{
				if(J.desglose.captura == ninguna && J.desglose.peso <= JugadaNormal)//PesoCaptura  && J.desglose.jaque == 0 ) 
				{
					ext_local = -1;
				}
			}
			if(ext_local == 0 && DoFutil && legales > 1 )
			{
				if(J.desglose.captura == ninguna &&  J.desglose.jaque == 0 &&  J.desglose.coronar == ninguna
					&& J.desglose.peso < PesoKiller)
					continue;
			}
		}
		Move(J);
		if(!Taux.EsAtacada(Taux.PosReyes[Taux.ColorJuegan^1],Taux.ColorJuegan^1))
		{
			legales++;
			PV[0] = '\0';
			if (fFoundPv) {
				value = -PVS(depth + ext_local - 1, -alpha-1, -alpha,PV,true);
				if ((value > alpha) && !cancelado) // Check for failure.
				{
					PV[0] = '\0';
					value = -PVS(depth - 1, -beta, -alpha,PV,true);
				}
			} else
			{
				PV[0] = '\0';
				value = -PVS(depth + ext_local - 1, -beta, -alpha,PV,true);
				if (ext_local < 0 && (value > alpha) && !cancelado) // Check for failure.
				{
					PV[0] = '\0';
					value = -PVS(depth - 1, -beta, -alpha,PV,true);
				}
			}
		assert(value > -MATE && value < MATE);
			if(legales == 1) // For nodeall save in TT the first move.
			{
				MejorJ = J.ToInt();
			}
		}
		TakeBack();
		if(cancelado) 
			break;

		if(value == -INFINITO )
			continue;
		assert(value > -MATE && value < MATE);
        if (value >= beta)
		{
#ifdef _DEBUG
			{
				strcpy(Global,J.ToString());
				strcat(Global," ");
				strcat(Global,PV);
			}
#endif
			if(J.desglose.captura == ninguna)
			{
				HashJ.SetKiller(stHistory,J.ToInt());
			}
			HashJ.Push(hash,J);
			if(depth > DepthCache)
				CACHEA(hash,beta,depth,LBOUND);
			PopHistory();
			assert(beta > -MATE && beta < MATE);
            return value; 
		}

        if (value > alpha)
		{
			if(!cancelado)
			{
				strcpy(Global,J.ToString());
				strcat(Global," ");
				strcat(Global,PV);
			}
			if(!cancelado && Depth <=  depth && stHistory == 1)
			{
				// new PV
				PrintInfo(value,Global);
				strcpy(JugadaActual,J.ToString());
				BestMoveActual = J;
			}
			HashJ.Push(hash,J);
			
            alpha = value;
			fFoundPv = true;
		}
    }
	if(legales == 0 && !cancelado)
	{
		if(EsJaque)
		{	// mate
			alpha = ValorMate(-1);
		}
		else
		{	// stalemate
			alpha = 0;
		}
	}

	PopHistory();
	if(!cancelado && !fFoundPv && legales > 0) // save first legal move for node all
	{
		J.Set(MejorJ);
		HashJ.Push(hash,J);
	}
	if(!cancelado && alpha && depth > DepthCache)
	{
		if(InPV)
		{
			CACHEA(hash,alpha,depth,EXACT);
		}
		else
			CACHEA(hash,alpha,depth,UBOUND);
	}
    return alpha;
}

