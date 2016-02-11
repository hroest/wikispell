#!/usr/bin/python
# -*- coding: utf-8  -*-


test_sample1 = u"""{{Infobox Chemikalie
| Name                = Aluminiumnitrat
| Strukturformel      = [[Datei:Al3+.svg|40px|Aluminiumion]] <math>\mathrm{ \
        \Biggl[}</math> [[Datei:Nitrat-Ion.svg|70px|Nitration]]<math>\mathrm{ \
        \!\ \Biggr]_3^{-}}</math>
| Andere Namen        = some text
}} and more text

== First text ==
Etiam sapien elit, euismod at mollis id, faucibus pharetra orci. Praesent id
purus mauris. '''Nam''' non <!-- sic! -->turpis lectus, vel congue velit.
Praesent cursus dictum est ut vestibulum. '''Pellentesque nec neque urna, in
pharetra justo.

== Links ==
[http://somecrazy.url.com Etiam sapien elit, euismod]
* [https://somecrazy.url.com Etiam sapien elit, euismod]

sollicitudin. Praesent venenatis volutpat ultricies. Fusce tincidunt diam in

    """

# alternative breaks
test_sample2 = u"""Cras commodo mollis elit, nec suscipit diam placerat ut.
Etiam sapien elit, euismod at mollis id, faucibus pharetra orci. Praesent id
purus mauris. '''Nam''' non turpis lectus, vel congue velit. Praesent cursus dictum
est ut vestibulum. '''Pellentesque nec neque urna, in pharetra justo.

Cras suscipit lorem eget elit pulvinar et molestie magna tempus. Vestibulum
eleifend '''felis''' nec lacus ultrices ut volutpat tortor auctor. Vivamus porta
vulputate tellus sed luctus. Sed viverra scelerisque feugiat. Pellentesque
habitant morbi tristique senectus et netus et malesuada fames ac turpis
egestas. Sed '''malesuada''' sapien ut massa interdum a sollicitudin odio
sollicitudin. Praesent venenatis volutpat ultricies. Fusce tincidunt diam in
nibh mattis quis consequat odio porttitor. <ref>Phasellus nec odio vitae nunc
lacinia condimentum a nec lorem. Etiam augue tortor, ornare in posuere ac,
mattis a nunc. '''In eu luctus orci. Nulla tellus dolor,</ref> lacinia nec
consequat at, rutrum eget dui. Morbi nulla justo, egestas id egestas luctus,
placerat vitae libero.  """

Kaliumpermanganat_rev73384760 = u"""{{Infobox Chemikalie
 | Name                = Kaliumpermanganat
 | Strukturformel      = [[Datei:K+.svg|20px|Kaliumion]] [[Datei:Permanganat-Ion2.svg|100px|Permanganation]]
 | Andere Namen        = *Kaliumtetraoxomanganat(VII)
* Kaliummanganat(VII)
* Übermangansaures Kali(um)
 | Summenformel        = KMnO<sub>4</sub>
 | ATC-Code            = *{{ATC|D08|AX06}}
*{{ATC|V03|AB18}}
 | CAS                 = 7722-64-7
 | Beschreibung        = violetter Feststoff<ref name="GESTIS"/>
 | Molare Masse        = 158,03 g·[[mol]]<sup>–1</sup>
 | Aggregat            = fest<ref name="GESTIS">{{GESTIS|Name=Kaliumpermanganat|CAS=7722-64-7|Datum=15. Dezember 2007}}</ref>
 | Dichte              = 2,70 g·cm<sup>–3</sup><ref name="GESTIS"/>
 | Schmelzpunkt        = zersetzt sich<ref name="GESTIS"/>
 | Siedepunkt          = 
 | Dampfdruck          = 1 [[Pascal (Einheit)|Pa]] (bei 20 °C)<ref name="GESTIS"/>
 | Löslichkeit         = mäßig in Wasser (64 g·l<sup>−1</sup> bei 20 °C)<ref name="GESTIS"/>
 | Quelle GefStKz      = {{RL|7722-64-7}}
 | Gefahrensymbole     = {{Gefahrensymbole|O|Xn|N}}
 | R                   = {{R-Sätze|8|22|50/53}}
 | S                   = {{S-Sätze|(2)|60|61}}
 | MAK                 = 0,5 mg·m<sup>–3</sup><ref name="GESTIS"/>
}}

'''Kaliumpermanganat''' (KMnO<sub>4</sub>) ist das [[Kalium]]salz der im freien Zustand unbekannten [[Permangansäure]], HMnO<sub>4</sub>. Es ist ein tief rot-violetter, metallisch glänzender, kristalliner Feststoff und ein starkes [[Oxidationsmittel]]. Für die intensive Färbung des Salzes ist ausschließlich das [[Permanganate|Permanganat]]-[[Anion]] verantwortlich. Die Farbe ist auf [[Charge-Transfer-Komplexe|Charge-Transfer-Übergänge]] zurückzuführen. In Permanganaten liegt das [[Mangan]] in seiner höchsten [[Oxidationszahl|Oxidationsstufe]] VII vor.

== Eigenschaften ==
Kaliumpermanganat bildet dunkle rot-violett glänzende Kristalle, die mäßig in Wasser löslich sind und schon in geringer Konzentration eine intensiv violette Lösung ergeben. Beim Erhitzen schmelzen die Kristalle nicht, sondern zerfallen ab ca. 240°C mit deutlichem Knistern unter [[Sauerstoff]]abgabe. Kristallines Kaliumpermanganat ist bei Raumtemperatur stabil, seine wässrigen Lösungen zersetzen sich aber mit der Zeit.

Da im Permanganat-Anion das Mangan in seiner höchsten Oxidationsstufe vorliegt, tritt es in [[Redoxreaktion]]en als ein sehr starkes [[Oxidationsmittel]] auf. So [[Oxidation|oxidiert]] Kaliumpermanganat z.B. [[Salzsäure]] zu [[Chlor]]gas (Labormethode zur Darstellung von Chlor):

"""

N_Chlorsuccinimid_rev80386547 = u"""{{DISPLAYTITLE:''N''-Chlorsuccinimid}}
{{Infobox Chemikalie
 | Strukturformel            = [[Datei:N-Chlorosuccinimide.svg|150px|Struktur von N-Chlorsuccinimid]]
 | Name                      = ''N''-Chlorsuccinimid
 | Andere Namen              = * NCS
* Succinchlorimid
* 1-Chlorpyrrolidin-2,5-dion
 | Summenformel              = C<sub>4</sub>H<sub>4</sub>ClNO<sub>2</sub>
 | CAS                       = 128-09-6
 | PubChem                   = 31398
 | Beschreibung              = weißer Feststoff mit Geruch nach Chlor<ref name="Merck"/>
 | Molare Masse              = 133,53 g·[[mol]]<sup>−1</sup>
 | Aggregat                  = fest
 | Dichte                    = 1,65 g·cm<sup>−3</sup><ref name="Merck">{{Merck|802811|Name={{PAGENAME}}|Datum=28. Februar 2010}}</ref>
 | Schmelzpunkt              = 148–151 [[Grad Celsius|°C]]<ref name="Merck"/>
 | Siedepunkt                = 216,5 °C<ref name="Merck"/>
 | Löslichkeit               = 14 g·l<sup>−1</sup> in Wasser (20 °C)<ref name="Merck"/>
 | Quelle GefStKz            = <ref name="Merck"/>
 | Gefahrensymbole           = {{Gefahrensymbole|C}}
 | R                         = {{R-Sätze|22|34|}}
 | S                         = {{S-Sätze|26|36/37/39|45}}
 | MAK                       = 
}}

'''''N''-Chlorsuccinimid''', meist kurz als '''NCS''' bezeichnet, ist das am [[Stickstoff]] chlorierte [[Imid]] der [[Bernsteinsäure]]. 

== Gewinnung und Darstellung ==
NCS kann durch Behandlung von [[Succinimid]] mit elementarem [[Chlor]] hergestellt werden.

== Verwendung ==
NCS wird im Labormaßstab vor allem als [[Chlorierung]]smittel eingesetzt, beispielsweise bei der Chlorierung von [[Alkene]]n in der [[Allyl]]stellung oder von Alkylaromaten in der [[Benzyl]]stellung. In größeren Mengen findet es bei der Produktion von pharmazeutischen Wirkstoffen (v.a. von [[Antibiotika]]) Verwendung. Verglichen mit elementarem [[Chlor]] (einem ätzenden, giftigen Gas) lässt sich NCS besser aufbewahren, handhaben und dosieren. Bei Umsatz von NCS entsteht als Nebenprodukt das wasserlösliche [[Succinimid]].

Die Verwendung von ''N''-Chlorsuccinimid als Chlorierungsmittel ist ein Beispiel für eine Synthesemethode, die mit geringer [[Atomökonomie]] abläuft.

== Einzelnachweise ==
<references/>

[[Kategorie:Chlorverbindung]]
[[Kategorie:Imid]]

[[en:N-Chlorosuccinimide]]
[[fr:N-Chlorosuccinimide]]
[[hu:N-klórszukcinimid]]
[[zh:N-氯代丁二酰亚胺]]
"""

Aluminiumnitrat_rev69770393  = u"""{{Infobox Chemikalie
| Name                = Aluminiumnitrat
| Strukturformel      = [[Datei:Al3+.svg|40px|Aluminiumion]] <math>\mathrm{ \ \Biggl[}</math> [[Datei:Nitrat-Ion.svg|70px|Nitration]]<math>\mathrm{ \ \!\ \Biggr]_3^{-}}</math>
| Andere Namen        = 
| Summenformel        = Al(NO<sub>3</sub>)<sub>3</sub>
| CAS                 = * 13473-90-0 (wasserfrei)
* 7784-27-2 (Nonahydrat)
| Beschreibung        = farbloser Feststoff<ref name=roempp>Helmut Sitzmann, in: ''Roempp Online - Version 3.5'', '''2009''', Georg Thieme Verlag, Stuttgart.</ref>
| Molare Masse        = * 212,99 [[Gramm|g]]·[[mol]]<sup>−1</sup> (wasserfrei)
* 375,13 g·mol<sup>−1</sup> (Nonahydrat)
| Aggregat            = fest
| Dichte              = 
| Schmelzpunkt        = Zersetzung ab 150 °C<ref name="BGIA GESTIS">{{GESTIS|Name=Aluminiumnitrat |ZVG=491034|CAS= |Datum=30. Oktober 2009}}</ref>
| Siedepunkt          = 
| Dampfdruck          = 
| Löslichkeit         = * sehr gut in Wasser (1370 g·[[Liter|l]]<sup>−1</sup> bei&nbsp;20&nbsp;°C)<ref name="BGIA GESTIS"/>
* löslich in [[Ethanol]]<ref name=roempp/>
| Quelle GefStKz      = <ref name="BGIA GESTIS"/>
| Gefahrensymbole     = {{Gefahrensymbole|O|Xi}}
| R                   = {{R-Sätze|8|36/38}}
| S                   = {{S-Sätze|17|26|36}}
| MAK                 = 
}}

'''Aluminiumnitrat''' ist eine [[chemische Verbindung]], das [[Aluminium]]salz der [[Salpetersäure]]. Es bildet farblose und zerfließliche [[Orthorhombisches Kristallsystem|rhombische]] Kristalle. Aluminiumnitrat ist sehr gut in Wasser löslich; die Lösung reagiert sauer.<ref>Römpp CD 2006, Georg Thieme Verlag 2006</ref> Beim Auskristallisieren aus wässrigen Lösungen bildet sich das Nona[[Kristallwasser|hydrat]] Al(NO<sub>3</sub>)<sub>3</sub>·9&nbsp;H<sub>2</sub>O. Beim Erhitzen gibt das Hydrat bei 73&nbsp;°C das Kristallwasser wieder ab. Das Salz zeigt keinen Schmelzpunkt und zersetzt sich ab etwa 150&nbsp;°C.<ref name="BGIA GESTIS"/>

== Synthese ==
Die Darstellung von Aluminiumnitrat kann durch Auflösen von [[Aluminiumhydroxid]] in Salpetersäure erfolgen.<ref name=roempp/>

:<math>\mathrm{Al(OH)_3\ +\ 3\ HNO_3\longrightarrow\ Al(NO_3)_3\ + 3\ H_2O}</math>

== Verwendung ==
Der Stoff wurde früher zur [[Glühstrumpf]]-Herstellung eingesetzt. Bei der Herstellung von [[Brennstab|Kernbrennstäben]] dient das Nitrat als [[Extraktionsmittel]] für Uran. Weiterhin wird Aluminiumnitrat als [[Beizen|Beize]] in der Färberei und zum [[Gerben]] von [[Leder]] verwendet.<ref name="BGIA GESTIS"/>

== Sicherheitshinweise ==
Aluminiumnitrat wirkt stark reizend auf die Schleimhäute der Augen und die Atemwege. Bei oraler Aufnahme können die aufgenommenen [[Nitrate|Nitrat]]ionen zu Schwindelgefühl, Kopfschmerzen sowie Schmerzen im Bauchbereich, blutigem Erbrechen, [[Diarrhoe]], Erschlaffung der Gefäßmuskulatur und Verringerung der Herzfrequenz führen. Das Nitrat ist ein starkes [[Oxidationsmittel]] und wirkt daher brandfördernd.<ref name="BGIA GESTIS"/>

== Quellen ==
<references />

[[Kategorie:Nitrat]]
[[Kategorie:Aluminiumverbindung]]

[[ar:نترات الألومنيوم]]
[[en:Aluminium nitrate]]
[[fa:آلومینیم نیترات]]
[[fr:Nitrate d'aluminium]]
[[it:Nitrato di alluminio]]
[[ja:硝酸アルミニウム]]
[[zh:硝酸铝]]
"""

Ubichinon10_rev73998553 = u"""
    {{SEITENTITEL:Coenzym Q<sub>10</sub>}}
    {{Infobox Chemikalie
    | Strukturformel  = [[Datei:CoenzymeQ10.svg|200px|Strukturformel von Coenzym Q10]]
    | Andere Namen    = * 2-[(2''E'',6''E'',10''E'',14''E'',18''E'',22''E'',26''E'',30''E'',34''E'')-<br />3,7,11,15,19,23,27,31,35,39-Decamethyltetraconta-2,6,10,14,18,22,26,30,34,38-decaenyl]-5,6-dimethoxy-3-methylcyclohexa-2,5-dien-1,4-dion ([[IUPAC]])
    * Ubichinon 10
    * CoQ<sub>10</sub>
    * Ubidecarenon
    | Summenformel    = C<sub>59</sub>H<sub>90</sub>O<sub>4</sub>
    | CAS             = 303-98-0
    | PubChem         = 5281915
    | Beschreibung    = 
    | Molare Masse    = 863,34 g·[[mol]]<sup>−1</sup>
    | Aggregat        = fest
    | Dichte          = <!-- g·cm<sup>−3</sup> -->
    | Schmelzpunkt    = 50 °C <ref name="Carl Roth" />
    | Siedepunkt      = <!-- °C -->
    | Dampfdruck      = <!-- [[Pascal (Einheit)|Pa]] ( °C) -->
    | Löslichkeit     = <!-- ??? löslich in ???:  g·l<sup>−1</sup> ( °C) -->
    | Quelle GefStKz  = <ref name="Carl Roth">{{Carl Roth|4047|Datum=12. April 2010}}</ref>
    | Gefahrensymbole = {{Gefahrensymbole|-}}
    | R               = {{R-Sätze|-}}
    | S               = {{S-Sätze|-}}
    | MAK             = <!-- ml·m<sup>−3</sup>, mg·m<sup>−3</sup> -->
    }}

    [[Datei:Ubichinon.svg|thumb|upright=1,39|Strukturformel der Ubichinone. Die Anzahl der Isopreneinheiten ist ''n'', beim Menschen ist ''n'' gewöhnlich 10.]]
    '''Coenzym Q<sub>10</sub>''' (auch '''Ubichinon 10''', '''UQ''', '''Coenzym Q''', '''CoQ''' oder '''Q''') ist ein [[Chinone|Chinon]]-Derivat mit [[lipophil]]er [[Isoprenoide|Isoprenoid]]-Seitenkette, strukturell verwandt mit [[Vitamin K]] und [[Vitamin E]]. Die reduzierte, phenolische Form wird '''Ubihydrochinon''' oder '''Ubichinol''' (kurz QH<sub>2</sub>) genannt. Den Namen „Ubichinon“ verdankt das [[Coenzym]] der Tatsache, dass es in allen lebenden Organismen verbreitet ist (lateinisch ''ubique'' = überall).

    """

Butylscopolaminbromid_rev69501497 = u"""
    {{Infobox Chemikalie
     | Strukturformel        = [[Datei:Butylscopolamine skeletal.svg|250px|Strukturformel von Butylscopolamin]] [[Datei:Br-.svg|x30px|Bromid]]
     | Freiname              = Butylscopolaminiumbromid
     | Andere Namen          = 
    * (1''R'',2''R'',4''S'',5''S'',7''s'',9''r'')-9-Butyl- 7-<nowiki>[[</nowiki>(2''S'')-3-hydroxy-2-phenylpropanoyl]- oxy]-9-methyl-3-oxa-9- azoniatricyclo<nowiki>[</nowiki>3.3.1.0<sup>2,4</sup>]nonanbromid
    * Butylscopolamin
    * ''N''-Butylscopolaminiumbromid
    *Hyoscinbutylbromid
    * Scopolaminbutylbromid
     | Summenformel          = C<sub>21</sub>H<sub>30</sub>BrNO<sub>4</sub>
     | CAS                   = 149-64-4
     | PubChem               = 160883
     | ATC-Code              = {{ATC|A03|BB01}}
     | DrugBank              = 
     | Wirkstoffgruppe       = * [[Parasympatholytikum]]
    * [[Spasmolytikum]]
     | Wirkmechanismus       = 
     | Verschreibungspflicht = teilweise ja
     | Molare Masse          = 440,37 [[Gramm|g]]·[[mol]]<sup>−1</sup>
     | pKs                   = 
     | Dichte                = 
     | Schmelzpunkt          = 142−144 °C <ref name="MerckIndex"> ''The [[Merck Index]]. An Encyclopaedia of Chemicals, Drugs and Biologicals''. 14. Auflage, 2006, S. 259, ISBN 978-0-911910-00-1.</ref>
     | Siedepunkt            = 
     | Dampfdruck            = 
     | Löslichkeit           = 
     | Quelle GefStKz        = <ref name="Ph. Eur.">[http://crs.edqm.eu/db/4DCGI/db/4DCGI/MSDS?MSDS=H1450000 Safety Data Sheet for ''HYOSCINE BUTYLBROMIDE CRS'', 22. März 2007] – [[Europäisches Direktorat für die Qualität von Arzneimitteln|EDQM]], eingesehen 5. Juni 2009</ref>
     | Gefahrensymbole       = {{Gefahrensymbole-klein|Xn}}
     | R                     = {{R-Sätze|20/22}}
     | S                     = {{S-Sätze|25|46}}
     | MAK                   = 
     | LD50                  = *1040 mg·kg<sup>−1</sup> (Ratte [[Peroral|p.o.]]) <ref name="Ph. Eur."/>
    * 24 mg (Ratte, i.v.) <ref name="Kleemann Engel">A. Kleemann, J. Engel, B. Kutscher, D. Reichert: ''Pharmaceutical Substances - Synthesis, Patents, Applications'', 4th Edition Thieme 2001, ISBN 3-13-115134-X</ref>
    * 1170 mg·kg<sup>−1</sup> (Maus [[Peroral|p.o.]]) <ref name="Kleemann Engel"/>
    * 10,3 mg (Maus, i.v.) <ref name="Kleemann Engel"/>
    }}

    '''Butylscopolaminbromid''', auch kurz '''Butylscopolamin''' ist ein [[Arzneistoff]] aus der Gruppe der [[Parasympatholytikum|Parasympatholytika]]. Es blockiert den [[Muskarinischer Acetylcholinrezeptor|muskarinischen Acetylcholinrezeptor]] und gehört damit zu den Muscarinrezeptor-Antagonisten. Dadurch wirkt der Arzneistoff krampflösend und wird in der Form seines [[Bromide|Bromid]]salzes '''''N''-Butylscopolaminiumbromid''' als [[Spasmolytikum]] eingesetzt.
    """
