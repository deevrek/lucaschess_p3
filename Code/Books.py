# This code is a translation to python from pg_key.c and pg_show.c released in the public domain by Michel Van den Bergh.
# http://alpha.uhasselt.be/Research/Algebra/Toga

import os
import random

from Code import ControlPosicion
from Code import Util
from Code import VarGen


class ListaLibros:
    def __init__(self):
        self.lista = []
        self.path = ""

        # S = Gestor solo
        # P = PGN
        # M = EntMaquina
        # T = Tutor
        self._modoAnalisis = ""

        self.alMenosUno()

    def recuperaVar(self, fichero):
        ll = Util.recuperaVar(fichero)
        if ll:
            self.lista = ll.lista
            self.path = ll.path
            self._modoAnalisis = ll._modoAnalisis
            self.alMenosUno()

    def guardaVar(self, fichero):
        Util.guardaVar(fichero, self)

    def alMenosUno(self):
        if len(self.lista) == 0:
            bookdef = VarGen.tbook
            b = Libro("P", bookdef.split("/")[1][:-4], bookdef, True)
            self.lista.append(b)

    def modoAnalisis(self, apli):
        return apli in self._modoAnalisis

    def porDefecto(self, book=None):
        if book:
            for book1 in self.lista:
                book1.pordefecto = False
            book.pordefecto = True
        else:
            self.alMenosUno()
            for book in self.lista:
                if book.pordefecto:
                    return book
            return self.lista[0]

    def cambiaModo(self, apli):
        if apli in self._modoAnalisis:
            self._modoAnalisis = self._modoAnalisis.replace(apli, "")
        else:
            self._modoAnalisis += apli

    def leeLibros(self, liLibros, fen, masTitulo, siPV):

        if not fen:
            return []

        posicion = ControlPosicion.ControlPosicion()
        posicion.leeFen(fen)
        p = Polyglot()
        ico = "w" if posicion.siBlancas else "b"
        icoL = "l"

        liResp = []
        for libro in liLibros:
            liResp.append((None, libro.nombre + masTitulo, icoL))
            li = p.lista(libro.path, fen)
            if li:
                total = 0
                for entry in li:
                    total += entry.weight

                for entry in li:
                    pv = entry.pv()
                    w = entry.weight
                    pc = w * 100.0 / total if total else "?"
                    pgn = posicion.pgnSP(pv[:2], pv[2:4], pv[4:])
                    liResp.append((pv if siPV else None, "%-5s -%7.02f%% -%7d" % (pgn, pc, w), ico))
            else:
                liResp.append((None, _("No result"), "c"))

        return liResp

    def comprueba(self):
        for x in range(len(self.lista) - 1, -1, -1):
            libro = self.lista[x]
            if not libro.existe():
                del self.lista[x]
        self.alMenosUno()

    def nuevo(self, libro):
        for libroA in self.lista:
            if libroA.igualque(libro):
                return
        self.lista.append(libro)

    def borra(self, libro):
        for n, libroL in enumerate(self.lista):
            if libroL == libro:
                del self.lista[n]

    def compruebaApertura(self, partida):
        liLibros = [libro for libro in self.lista if libro.pordefecto]
        if (not liLibros) and self.lista:
            liLibros = [self.lista[0]]

        p = Polyglot()
        icoL = "l"

        liResp = []
        for nlibro, libro in enumerate(liLibros):
            liResp.append((None, libro.nombre, icoL, None))
            for njug, jg in enumerate(partida.liJugadas):
                posicion = jg.posicionBase
                li = p.lista(libro.path, posicion.fen())
                if li:
                    total = 0
                    for entry in li:
                        total += entry.weight
                    pv = jg.movimiento()

                    ok = False

                    liOp = []
                    for entry in li:
                        w = entry.weight
                        pct = w * 100.0 / total if total else "-"
                        pvt = entry.pv()
                        pgn = posicion.pgnSP(pvt[:2], pvt[2:4], pvt[4:])
                        liOp.append("%-5s -%7.02f%% -%7d" % (pgn, pct, w))
                        if pv == pvt:
                            ok = True
                            pc = pct

                    if jg.posicionBase.siBlancas:
                        ico = "w"
                        previo = "%2d." % partida.numJugadaPGN(njug)
                        posterior = "   "
                    else:
                        ico = "b"
                        previo = "      "
                        posterior = ""
                    pgn = jg.pgnSP()
                    puntos = "%7.02f%%" % pc if ok else "   ???"

                    liResp.append(
                            ("%d|%d" % (nlibro, njug), "%s%-5s%s - %s" % (previo, pgn, posterior, puntos), ico, liOp))
                    if not ok:
                        break

        return liResp


class Libro:
    def __init__(self, tipo, nombre, path, pordefecto, extras=None):
        self.tipo = tipo
        self.nombre = nombre
        self.path = path
        self.pordefecto = pordefecto
        self.orden = 100  # futuro ?
        self.extras = extras  # futuro ?

    def igualque(self, otro):
        return self.tipo == otro.tipo and \
               self.nombre == otro.nombre and \
               self.path == otro.path

    def existe(self):
        return os.path.isfile(self.path)

    def polyglot(self):
        self.book = Polyglot()

    def miraListaJugadas(self, fen):
        li = self.book.lista(self.path, fen)
        posicion = ControlPosicion.ControlPosicion()
        posicion.leeFen(fen)

        total = 0
        maxim = 0
        for entry in li:
            w = entry.weight
            total += w
            if w > maxim:
                maxim = w

        listaJugadas = []
        for entry in li:
            pv = entry.pv()
            w = entry.weight
            pc = w * 100.0 / total if total else "?"
            desde, hasta, coronacion = pv[:2], pv[2:4], pv[4:]
            pgn = posicion.pgnSP(desde, hasta, coronacion)
            listaJugadas.append((desde, hasta, coronacion, "%-5s -%7.02f%% -%7d" % (pgn, pc, w), 1.0 * w / maxim))
        return listaJugadas

    def eligeJugadaTipo(self, fen, tipo):
        maxim = 0
        liMax = []
        li = self.book.lista(self.path, fen)
        nli = len(li)
        if nli == 0:
            return None

        elif nli == 1:
            pv = li[0].pv()

        elif tipo == "mp":  # Mejor posicion
            for entry in li:
                w = entry.weight
                if w > maxim:
                    maxim = w
                    liMax = [entry]
                elif w == maxim:
                    liMax.append(entry)
            pos = random.randint(0, len(liMax) - 1) if len(liMax) > 1 else 0
            pv = liMax[pos].pv()

        elif tipo == "au":  # Aleatorio uniforme
            pos = random.randint(0, len(li) - 1)
            pv = li[pos].pv()

        elif tipo == "ap":  # Aleatorio proporcional
            liW = [x.weight for x in li]
            t = sum(liW)
            num = random.randint(1, t)
            pos = 0
            t = 0
            for n, x in enumerate(liW):
                t += x
                if num <= t:
                    pos = n
                    break
            pv = li[pos].pv()

        else:
            return None

        return pv.lower()

    def miraListaPV(self, fen, siMax):
        li = self.book.lista(self.path, fen)

        liResp = []
        if siMax:
            maxim = -1
            for entry in li:
                w = entry.weight
                if w > maxim:
                    maxim = w
                    liResp = [entry.pv()]
                    # elif w == maxim:
                    # liResp.append(entry.pv())
        else:
            for entry in li:
                liResp.append(entry.pv())

        return liResp


class Entry:
    key = 0
    move = 0
    weight = 0
    learn = 0

    def pv(self):
        move = self.move

        f = (move >> 6) & 0o77
        fr = (f >> 3) & 0x7
        ff = f & 0x7
        t = move & 0o77
        tr = (t >> 3) & 0x7
        tf = t & 0x7
        p = (move >> 12) & 0x7
        pv = chr(ff + ord('a')) + chr(fr + ord('1')) + chr(tf + ord('a')) + chr(tr + ord('1'))
        if p:
            pv += " nbrq"[p]

        return {"e1h1": "e1g1", "e1a1": "e1c1", "e8h8": "e8g8", "e8a8": "e8c8"}.get(pv, pv)


class Polyglot:
    """
        fen = "rnbqkbnr/pppppppp/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        fich = "varied.bin"

        p = Polyglot()
        li = p.lista( fich, fen )

        for entry in li:
            p rint entry.pv(), entry.weight
    """

    random64 = (
        11329126462075137345, 3096006490854172103, 4961560858198160711, 11247167491742853858, 8467686926187236489,
        3643601464190828991,
        1133690081497064057, 16733846313379782858, 972344712846728208, 1875810966947487789, 10810281711139472304,
        14997549008232787669,
        4665150172008230450, 77499164859392917, 6752165915987794405, 2566923340161161676, 419294011261754017,
        7466832458773678449,
        8379435287740149003, 9012210492721573360, 9423624571218474956, 17519441378370680940, 3680699783482293222,
        5454859592240567363,
        12278110483549868284, 10213487357180498955, 9786892961111839255, 1870057424550439649, 13018552956850641599,
        8864492181390654148,
        14503047275519531101, 2642043227856860416, 5521189128215049287, 1488034881489406017, 12041389016824462739,
        236592455471957263,
        7168370738516443200, 707553987122498196, 3852097769995099451, 8313129892476901923, 1761594034649645067,
        2291114854896829159,
        15208840396761949525, 13805854893277020740, 11490038688513304612, 5903053950100844597, 6666107027411611898,
        18228317886339920449,
        3626425922614869470, 10120929114188361845, 13383691520091894759, 9148094160140652064, 1284939680052264319,
        7307368198934274627,
        5611679697977124792, 10869036679776403037, 4819485793530191663, 7866624006794876513, 4794093907474700625,
        6849775302623042486,
        4177248038373896072, 10648116955499083915, 7195685255425235832, 17012007340428799350, 6004979459829542343,
        575228772519342402,
        5806056339682094430, 8920438500019044156, 1872523786854905556, 7168173152291242201, 9388215746117386743,
        8767779863385330152,
        1489771135892281206, 17385502867130851733, 15762364259840250620, 2649182342564336630, 13505777571156529898,
        928423270205194457,
        11861585534482611396, 16833723316851456313, 2875176145464482879, 9598842341590061041, 6103491276194240627,
        8264435384771931435,
        17191732074717978439, 11134495390804798113, 8118948727165493749, 17994305203349779906, 9778408473133385649,
        11774350857553791160,
        12559012443159756018, 1810658488341658557, 9781539968129051369, 658149708018956377, 18376927623552767184,
        10225665576382809422,
        11247233359009848457, 12966474917842991341, 4111328737826509899, 6628917895947053289, 2166287019647928708,
        11129710491401161907,
        5728850993485642500, 7135057069693417668, 2409960466139986440, 6600979542443030540, 5794634036844991298,
        1765885809474863574,
        7278670237115156036, 16128398739451409575, 17262998572099182834, 8877430296282562796, 13401997949814268483,
        407550088776850295,
        13080877114316753525, 5365205568318698487, 14935709793025404810, 17669982663530100772, 4357691132969283455,
        17142609481641189533,
        8763584794241613617, 9679198277270145676, 10941274620888120179, 11693142871022667058, 306186389089741728,
        10524424786855933342,
        8136607301146677452, 8332101422058904765, 6215931344642484877, 17270261617132277633, 13484155073233549231,
        5040091220514117480,
        10596830237594186850, 18403699292185779873, 12565676100625672816, 15937214097180383484,
        9145986266726084057, 2521545561146285852,
        14490332804203256105, 9262732965782291301, 16052069408498386422, 2012514900658959106, 4851386166840481282,
        12292183054157138810,
        12139508679861857878, 7319524202191393198, 16056131139463546102, 2445601317840807269, 12976440137245871676,
        10500241373960823632,
        1211454228928495690, 2931510483461322717, 14252799396886324310, 6217490319246239553, 3253094721785420467,
        11224557480718216148,
        17235000084441506492, 12619159779355142232, 5189293263797206570, 12606612515749494339, 1850950425290819967,
        5933835573330569280,
        17649737671476307696, 1240625309976189683, 13611516503114563861, 11359244008442730831, 463713201815588887,
        5603848033623546396,
        5837679654670194627, 13869467824702862516, 13001586210446667388, 12934789215927278727, 2422944928445377056,
        3310549754053175887,
        8519766042450553085, 17839818495653611168, 15503797852889124145, 16011257830124405835, 862037678550916899,
        3197637623672940211,
        5210919022407409764, 14971170165545012763, 12708212522875260313, 11160345150269715688,
        11888460494489868490, 16669255491632516726,
        7618258446600650238, 17993489941568846998, 18188493901990876667, 11270342415364539415,
        10288892439142166224, 7423022476929853822,
        14215600671451202638, 8710936142583354014, 18346051800474256890, 629718674134230549, 10598630096540703438,
        10666243034611769205,
        16077181743459442704, 4303848835390748061, 15183795910155040575, 17843919060799288312,
        15561328988693261185, 15662367820628426663,
        3706272247737428199, 12051713806767926385, 11742603550742019509, 5704473791139820979, 9787307967224182873,
        1637612482787097121,
        8908762506463270222, 17556853009980515212, 4157033003383749538, 18207866109112763428, 1800584982121391508,
        5477894166363593411,
        4674885479076762381, 10160025381792793281, 7550910419722901151, 8799727354050345442, 11321311575067810671,
        4039979115090434978,
        3605513501649795505, 3876110682321388426, 12180869515786039217, 8620494007958685373, 5854220346205463345,
        4855373848161890066,
        15654983601351599195, 5949110547793674363, 5957016279979211145, 11321480117988196211, 8228060533160592200,
        2094843038752308887,
        8801329274201873314, 297395810205168342, 6489982145962516640, 925952168551929496, 6268205602454985292,
        2903841526205938350,
        359914117944187339, 8371662176944962179, 11139146693264846140, 9807576242525944290, 5795683315677088036,
        12688959799593560697,
        1070089889651807102, 6778454470502372484, 17760055623755082862, 1983224895012736197, 15760908081339863073,
        942692161281275413,
        12134286529149333529, 10647676541963177979, 11090026030168016689, 5245566602671237210, 9195060651485531055,
        6368791473535302177,
        3229483537647869491, 15232282204279634326, 928484295759785709, 1909608352012281665, 10412093924024305118,
        5773445318897257735,
        3990834569972524777, 10771395766813261646, 4209783265310087306, 15318153364378526533, 616435239304311520,
        17961392050318287288,
        7798983577523272147, 3913469721920333102, 15424667983992144418, 6239239264182308800, 1654244791516730287,
        17228895932005785491,
        6221161860315361832, 17056602083001532789, 13458912522609437003, 12917665617485216338, 7337288846716161725,
        13022188282781700578,
        12979943748599740071, 510457344639386445, 8796640079689568245, 13565008864486958290, 6465331256500611624,
        11031297210088248644,
        8017026739316632057, 3627975979343775636, 15052215649796371267, 6222903725779446311, 3527832623857636372,
        15597050972685397327,
        8924250025456295612, 14400806714161458836, 10699110515857614396, 14468157413083537247, 4223238849618215370,
        15681850266533497060,
        1140009269240963018, 12966521765762216121, 12695701950206930564, 3881319844097050799, 16858671235974049358,
        17004178443650550617,
        10544522896658866816, 13378871666599081203, 7580967567056532817, 14279886347066493375,
        14791316027199525482, 13540141887354822347,
        15889873206108611120, 13441296750672675768, 11798467976251859403, 16858792058461978657, 704784010218719535,
        9596982322589424841,
        9297677921824001878, 687173692492309888, 2573542046251205823, 14064986013008197277, 5122261027125484554,
        12166444546397347981,
        392580029432520891, 13077660124902070727, 16778702188287612735, 3451078315256158032, 1238907336018749328,
        9205113463181886956,
        1667962162104261376, 10830753981784044039, 4479827962372740717, 13723669708721922220, 17895945165757891767,
        5275192813757817777,
        2148246364622112874, 2290795724393258885, 18193581350273252090, 1776293542351822525, 14757011774120772237,
        4313244667902787366,
        12281515972708701602, 16810874891151093887, 13231770820477907822, 15338037979535853741,
        3321611548688927336, 3305807524324674332,
        13385011844708802686, 7248312053715383136, 10692263740491040132, 15834887971838928217,
        15164530629649278767, 9112428691881135949,
        7848957776938116907, 10951816186743012388, 8896660382367628050, 9603906275513256852, 8762207035762213579,
        14987444343672838948,
        9409751230138127831, 10591026249259463665, 7197363620976276483, 14301381657157454364, 6373588016705149671,
        685071415365890925,
        11485719029193745472, 11525714121369126191, 16463451990009075596, 16713578179004591821,
        6251124536988276734, 6144308296388004591,
        8880818733894805775, 1303007271453773655, 9174156641096830119, 8824404812019774483, 4420129794615782201,
        9951556838786075828,
        8883975763174874978, 10736884308676275715, 5595889224692918441, 4306406647446967767, 6704191827946442961,
        9195534799547011879,
        15724940538984617905, 15915014237009546277, 3928039610514994951, 14873195079178728329,
        12362539403674935092, 4869881251581666789,
        12986343614603388393, 1215083005313393810, 15835354158744478399, 11186056805483324290,
        13149236123055901828, 13821214860367539280,
        12182689304549523133, 2305696533800337221, 12399248800711438055, 12612571074767202621, 1949121388445288260,
        13067734303660960050,
        14085928898807657146, 14099042149407050217, 17561987301945706495, 11512458344154956250,
        7437568954088789707, 7915171836405846582,
        11752651295154297649, 520574178807700830, 9984063241072378277, 16254155646211095029, 8412807604418121470,
        5609875541891257226,
        11323858615586018348, 8376971840073549054, 1383314287233606303, 15474222835752021056, 5204145074798490767,
        2167677454434536938,
        10341418833443722943, 8271005071015654673, 15537457915439920220, 10730891177390075310,
        11511496483171570656, 16026237624051288806,
        11839117319019400126, 11321351259605636133, 5895970210948560438, 3447475526873961356, 7334775646005305872,
        15954460007382865005,
        6939292427400212706, 8334626163711782046, 1912937584935571784, 12304971244567641760, 8524679326357320614,
        2204997376562282123,
        3197166419597805379, 4220875528993937793, 2803169229572255230, 5085503808422584221, 14444799216525086860,
        4570145336765972565,
        9186432380899140933, 11239615222781363662, 9872907954749725788, 10369691348610460342, 11573842626212501214,
        18049927275724560211,
        15471783285232223897, 16134745906572777443, 13149419803421182712, 14564139292183438565,
        2088698177441502777, 15099871677732932330,
        5679318949880730421, 16491038769688081874, 1684901764271550206, 6019498834983443029, 8308552077872645018,
        2774412133178445207,
        2993471197969887147, 8756104692490586069, 7404378077533100169, 11391825116471223489, 17128408637045999621,
        5816122712455824169,
        5531291136777113635, 7400684525794093602, 2421696223438995901, 2746718911238191773, 2297623779240041360,
        15514986454711725499,
        13355177993350187464, 2151598180055853022, 14933732441462847914, 17651243408385815107, 4086544267540179726,
        3960368502933186560,
        16948614951473504462, 11262612224635188739, 12613511070148831882, 2706199935239343179,
        10054459213633325149, 17640957734094436437,
        15290986714861486531, 16616573458614039565, 2626432152093131908, 14024745482209308341,
        12344195406125417964, 7167044992416702836,
        11933989054878784040, 1255659969011027721, 3240842176865726111, 795178308456769763, 12389083385239203825,
        6408553047871587981,
        14331996049216472800, 3362936192376505047, 1486633608756523830, 8937438391818961808, 15513702763578092231,
        9242607645174922067,
        16999375738341892551, 225631029947824688, 5294122026845313316, 11666909141406975304, 6576914768872977647,
        13014342141693467190,
        15296769519938257969, 1344590668019013826, 8870296219354404, 1763076921063072981, 11710831831040350446,
        11042296215092253456,
        12923501896423220822, 2679459049130362043, 15149139477832742400, 2006921612949215342, 2441159149980359103,
        4254066403785111886,
        10165995291879048302, 17968517685540419316, 4067155115498534723, 14584673823956990486, 7262306400971602773,
        2599246507224983677,
        1183331494191622178, 9203696637336472112, 8684305384778066392, 452576500022594089, 7158260433795827572,
        5749101480176103715,
        2141838636388669305, 13319697665469568251, 11739738846189583585, 15704600611932076809,
        17288566729036156523, 3345333136360207999,
        12225668941959679643, 13135848755558586049, 8127707564878445808, 11020438739076919854,
        13800233257954351967, 10719452353263111411,
        4467639418469323241, 13341252870622785523, 7043015398453076736, 13802777531561938248, 2597087673064131360,
        18196619797102886407,
        17222554220133987378, 11603572837337492490, 9373650498706682568, 15247985213323458255, 2826050093225892884,
        7047939442312345917,
        1975862676241125979, 8471065344236531211, 10781433328192619353, 12710259184248419661, 6983092299355911633,
        8891398163252015007,
        18232837537224201402, 10128874404256367960, 1184291664448112016, 8752186474456668498, 11883874832968622155,
        8304258407043758711,
        13031437632736158055, 11394657882570178521, 11346359947151974253, 15207539437603825135,
        6743071165850287963, 1895531807983368793,
        8070015023023620019, 15994912017468668362, 7264555371116116147, 638838107884199779, 612060626599877907,
        16368581545287660539,
        2028126038944990910, 8217932366665821866, 12715716898990721499, 4917760284400488853, 4689038209317479950,
        15570055495392019914,
        7353589116749496814, 6461588461223219363, 16737230234434607639, 10643751583066909176, 13889371344374910415,
        14623784806974468748,
        6280119077769544053, 5795026310427216669, 15581542564775929183, 5344020438314994897, 17090582320435646615,
        13070392342864893666,
        2499216570383001617, 5973851566933180981, 11163195574208743088, 10686881252049739702, 7802414647854227001,
        7696730671131205892,
        11939552629336260711, 8954801150602803298, 5805966293032425995, 10608482480047230587, 4997389530575201269,
        7710978612650642680,
        7716832357345836839, 15123312752564224361, 16000314919358148208, 5766400084981923062, 11245886267645737076,
        8713884558928322285,
        7910921931260759656, 17192478743862940141, 3651028258442904531, 4208705969817343911, 3568641929344250749,
        7493701010274154640,
        2245920858524015772, 13159017457951468389, 12290633441485835508, 17599068061438200851,
        18107352842948477138, 3841784002685309084,
        3972025232192455038, 7780701379940603769, 14773200954226001784, 16368109790951669962, 11498059885876068682,
        331717439817162336,
        18209951341142539931, 639100052003347099, 10347169565922244001, 13093097841025825382, 2526013881820679475,
        4894708394808468861,
        4217798054095379555, 2415982786774940751, 2008219703699744969, 6034935405124924712, 16377935039880138091,
        15469949637801139582,
        6813989660423069229, 3171782229498906237, 12757488664123869734, 4587441767303016857, 1011542511767058351,
        1218420902424652599,
        11452069637570869555, 15332250653395824223, 9318912313336593440, 10499356348280572422,
        17042034373048666488, 1805505087651779950,
        13083730121955101027, 9926866826056072641, 12395083137174176754, 13014086693993705056,
        18092419734315653769, 4496402702769466389,
        4275128525646469625, 16718947186147009622, 2644524053331857687, 16665345306739798209, 756689505943647349,
        6332958748006341455,
        5397518675852254155, 3282372277507744968, 15124857616913606283, 9958173582926173484, 550475751710050266,
        9535384695938759828,
        11027794851313865315, 1895999114042080393, 17795970715748483584, 3512907883609256988, 10170876972722661254,
        5100888107877796098,
        14766188770308692257, 5664728055166256274, 1867780161745570575, 5069314540135811628, 10826357501146152497,
        8428576418859462269,
        6489498281288268568, 248384571951887537, 14408891171920865889, 3830179243734057519, 10976374785232997173,
        12375273678367885408,
        14917570089431431088, 5317296011783481118, 8812437177215009958, 15702128452263965086, 1418237564682130775,
        8287918193617750527,
        5641726496814939044, 18399300296243087930, 6176181444192939950, 13286219625023629664, 14609847597738937780,
        15778618041730427743,
        13113915167160321176, 3534397173597697283, 16753315048725296654, 2378655170733740360, 17894101054940110861,
        551298419243755034,
        14177640314441820846, 18011171644070679608, 1942137629605578202, 17704970308598820532,
        10820688583425137796, 319261663834750185,
        17320020179565189708, 10828766552733203588, 11254165892366229437, 5921710089078452638, 1692791583615940497,
        3154220012138640370,
        2462272376968205830, 5215882904155809664, 9063345109742779520, 10012495044321978752, 2282028593076952567,
        16490284710305269338,
        11358175869672944140, 2648366387851958704, 2535530668932196013, 15386192992268326902, 6797681746413993003,
        9131737009282615627,
        744965241806492274, 15534171479957703942, 11406512201534848823, 1724859165393741376, 2131804225590070214,
        10649852818715990109,
        7348272751505534329, 15418610264624661717, 14030296408486517359, 6426639016335384064, 14857241317133980380,
        8982836549816060296,
        2847738978322528776, 14275200949057556108, 1517491100508351526, 11487065943069529588, 7252270709068430025,
        1454069630547688509,
        879136823698237927, 764541931096396549, 16628452526739142958, 8210570252116953863, 17419012767447246106,
        16656819168530874484,
        10879562253146277412, 9340840147615694245, 6892625624787444041, 6239858431661771035, 10484131262376733793,
        15135908441777759839,
        3591372000141165328, 17394508730963952016, 11925077963498648480, 2231224496660291273, 8127998803539291684,
        16292452481085749975,
        16488107566197090, 2060923303336906913, 14929791059677233801, 15052228947759922034, 8630622898638529667,
        7467898009369859339,
        17930561480947107081, 18287077397422080,)

    randomPiece = random64
    randomCastle = random64[768:]
    randomEnPassant = random64[772:]
    randomTurn = random64[780:]

    piece_names = "pPnNbBrRqQkK"

    def hash(self, fen):

        board_s, to_move_c, castle_flags_s, ep_square_s, mp, jg = fen.split(" ")

        board = []
        for f in range(8):
            li = []
            board.append(li)
            for r in range(8):
                li.append("-")

        key = 0

        r = 7
        f = 0
        p = 0
        lb = len(board_s)

        while p < lb:
            c = board_s[p]
            p += 1

            if c == '/':
                r -= 1
                f = 0

            elif '1' <= c <= '8':
                f += int(c)

            else:
                board[f][r] = c
                f += 1
        for f in range(8):
            for r in range(8):
                c = board[f][r]
                if c != '-':
                    p_enc = self.piece_names.index(c)
                    key ^= self.randomPiece[64 * p_enc + 8 * r + f]
        p = 0
        lb = len(castle_flags_s)

        while p < lb:
            c = castle_flags_s[p]
            p += 1

            if c == 'K':
                key ^= self.randomCastle[0]
            elif c == 'Q':
                key ^= self.randomCastle[1]
            elif c == 'k':
                key ^= self.randomCastle[2]
            elif c == 'q':
                key ^= self.randomCastle[3]

        if ep_square_s != '-':
            f = ord(ep_square_s[0]) - ord('a')
            if to_move_c == 'b':
                if (f > 0 and board[f - 1][3] == 'p') or (f < 7 and board[f + 1][3] == 'p'):
                    key ^= self.randomEnPassant[f]
            else:
                if (f > 0 and board[f - 1][4] == 'P') or (f < 7 and board[f + 1][4] == 'P'):
                    key ^= self.randomEnPassant[f]

        if to_move_c == 'w':
            key ^= self.randomTurn[0]

        return key

    def int_from_file(self, l, r):
        cad = self.f.read(l)

        if len(cad) != l:
            return True, 0
        for c in cad:
            r = (r << 8) + c
        return False, r

    def entry_from_file(self):

        entry = Entry()

        r = 0
        ret, r = self.int_from_file(8, r)
        if ret:
            return True, None
        entry.key = r

        ret, r = self.int_from_file(2, r)
        if ret:
            return True, None
        entry.move = r & 0xFFFF

        ret, r = self.int_from_file(2, r)
        if ret:
            return True, None
        entry.weight = r & 0xFFFF

        ret, r = self.int_from_file(4, r)
        if ret:
            return True, None
        entry.learn = r & 0xFFFFFFFF

        return False, entry

    def find_key(self, key):

        first = -1
        try:
            if not self.f.seek(-16, os.SEEK_END):
                entry = Entry()
                entry.key = key + 1
                return -1, entry
        except Exception as e:
            return -1, None

        last = self.f.tell() // 16
        ret, last_entry = self.entry_from_file()
        while True:
            if last - first == 1:
                return last, last_entry

            middle = (first + last) // 2
            self.f.seek(16 * middle, os.SEEK_SET)
            ret, middle_entry = self.entry_from_file()
            if key <= middle_entry.key:
                last = middle
                last_entry = middle_entry
            else:
                first = middle

    def lista(self, fichero, fen):
        key = self.hash(fen)

        self.f = open(fichero, "rb")

        offset, entry = self.find_key(key)
        li = []
        if entry and entry.key == key:

            li.append(entry)

            self.f.seek(16 * (offset + 1), os.SEEK_SET)
            while True:
                ret, entry = self.entry_from_file()
                if ret or (entry.key != key):
                    break

                li.append(entry)

        self.f.close()
        del self.f

        return li

        # def listaJugadas( self, fen ):
        # li = self.lista( self.path, fen )
        # posicion = ControlPosicion.ControlPosicion()
        # posicion.leeFen( fen )

        # total = 0
        # maxim = 0
        # for entry in li:
        # w = entry.weight
        # total += w
        # if w > maxim:
        # maxim = w

        # listaJugadas = []
        # for entry in li:
        # pv = entry.pv()
        # w = entry.weight
        # pc = w*100.0/total if total else "?"
        # desde, hasta, coronacion = pv[:2], pv[2:4], pv[4:]
        # pgn = posicion.pgnSP( desde, hasta, coronacion )
        # listaJugadas.append( ( desde, hasta, coronacion, "%-5s -%7.02f%% -%7d"%( pgn, pc, w), 1.0*w/maxim ) )
        # return listaJugadas
