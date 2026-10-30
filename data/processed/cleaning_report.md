# Bereinigungsbericht Phase 1 (automatisch erzeugt)

- Eingabe: `ESS.csv` (SHA-256 `4b0bfa73fa86bcf9…`)
- Ergebnis: 2262 Personen, Profil 258 Spalten, Fragebogen 22 Spalten

| Schritt | Beschreibung | Profil (Zeilen × Spalten) | Fragebogen | Zeilen entfernt | Spalten entfernt | Zellen geleert |
|---|---|---|---|---|---|---|
| 1 | Original-CSV eingelesen | 50116 × 691 | – | 0 | 0 | 0 |
| 2 | Split in Profil und Fragebogen | 50116 × 671 | 50116 × 22 | 0 | 0 | 0 |
| 3 | Nur cntry == DE | 2420 × 671 | 2420 × 22 | 47696 | 0 | 0 |
| 4 | Komplett leere Spalten gelöscht | 2420 × 420 | 2420 × 22 | 0 | 251 | 0 |
| 5 | Spalten mit > 50% Wert 0 gelöscht | 2420 × 293 | 2420 × 22 | 0 | 127 | 0 |
| 6 | Missing-Codes durch leere Zellen ersetzt | 2420 × 293 | 2420 × 22 | 0 | 0 | 133376 |
| 7 | Personen mit ≥ 1 unbeantworteter Frage entfernt | 2262 × 293 | 2262 × 22 | 158 | 0 | 0 |
| 8 | Interview-Metadaten und doppelte Kodierungen gelöscht | 2262 × 258 | 2262 × 22 | 0 | 35 | 0 |

## Schritt 2 – Split in Profil und Fragebogen

ID = <cntry>_<idno>

## Schritt 4 – Komplett leere Spalten gelöscht

Gelöschte Spalten (251): `prtvtdat`, `prtvtebe`, `prtvtfbg`, `prtvtchr`, `prtvtccy`, `prtvtiee`, `prtvtffi`, `prtvtffr`, `prtvtegr`, `prtvthhu`, `prtvteis`, `prtvteie`, `prtvteil`, `prtvteit`, `prtvtblv`, `prtvclt1`, `prtvclt2`, `prtvclt3`, `prtvtbme`, `prtvtinl`, `prtvtcno`, `prtvtfpl`, `prtvtept`, `prtvtbrs`, `prtvtesk`, `prtvtgsi`, `prtvtges`, `prtvtese`, `prtvthch`, `prtvtdua`, `prtvtdgb`, `prtcleat`, `prtclebe`, `prtclfbg`, `prtclbhr`, `prtclccy`, `prtcliee`, `prtclgfi`, `prtclgfr`, `prtclegr`, `prtclihu`, `prtcleis`, `prtclfie`, `prtclfil`, `prtclfit`, `prtclblv`, `prtclclt`, `prtclbme`, `prtclhnl`, `prtclcno`, `prtcljpl`, `prtclgpt`, `prtclbrs`, `prtclesk`, `prtclgsi`, `prtclhes`, `prtclese`, `prtclhch`, `prtcleua`, `prtcldgb`, `rlgdnbat`, `rlgdncy`, `rlgdnafi`, `rlgdnagr`, `rlgdnhu`, `rlgdnais`, `rlgdnie`, `rlgdnlv`, `rlgdnlt`, `rlgdme`, `rlgdnanl`, `rlgdnno`, `rlgdnapl`, `rlgdnapt`, `rlgdnrs`, `rlgdnask`, `rlgdnase`, `rlgdnach`, `rlgdnaua`, `rlgdngb`, `rlgdebat`, `rlgdecy`, `rlgdeafi`, `rlgdeagr`, `rlgdehu`, `rlgdeais`, `rlgdeie`, `rlgdelv`, `rlgdelt`, `rlgdeme`, `rlgdeanl`, `rlgdeno`, `rlgdeapl`, `rlgdeapt`, `rlgders`, `rlgdeask`, `rlgdease`, `rlgdeach`, `rlgdeaua`, `rlgdegb`, `vteubcmb`, `gndr7`, `gndr8`, `gndr9`, `gndr10`, `gndr11`, `gndr12`, `gndr13`, `yrbrn7`, `yrbrn8`, `yrbrn9`, `yrbrn10`, `yrbrn11`, `yrbrn12`, `yrbrn13`, `rshipa7`, `rshipa8`, `rshipa9`, `rshipa10`, `rshipa11`, `rshipa12`, `rshipa13`, `rshipa15`, `edlveat`, `edlvebe`, `edlvebg`, `edlvehr`, `edlvgcy`, `edlvdee`, `edlvdfi`, `edlvdfr`, `edlvegr`, `edlvdahu`, `edlvdis`, `edlvdie`, `edubil1`, `eduail2`, `edlvfit`, `edlvelv`, `edlvdlt`, `edlveme`, `edlvenl`, `edlveno`, `edlvipl`, `edlvept`, `edlvdrs`, `edlvdsk`, `edlvesi`, `edlvies`, `edlvdse`, `edlvdch`, `edlvdua`, `educgb1`, `edubgb2`, `edagegb`, `edlvpfat`, `edlvpebe`, `edlvpebg`, `edlvpehr`, `edlvpgcy`, `edlvpdee`, `edlvpdfi`, `edlvpdfr`, `edlvpegr`, `edlvpdahu`, `edlvpdis`, `edlvpdie`, `edupail2`, `edupbil1`, `edlvpfit`, `edlvpelv`, `edlvpdlt`, `edlvpeme`, `edlvpenl`, `edlvpeno`, `edlvphpl`, `edlvpept`, `edlvpdrs`, `edlvpdsk`, `edlvpesi`, `edlvphes`, `edlvpdse`, `edlvpdch`, `edlvpdua`, `edupcgb1`, `edupbgb2`, `edagepgb`, `edlvfeat`, `edlvfebe`, `edlvfebg`, `edlvfehr`, `edlvfgcy`, `edlvfdee`, `edlvfdfi`, `edlvfdfr`, `edlvfegr`, `edlvfdahu`, `edlvfdis`, `edlvfdie`, `edufbil1`, `edufail2`, `edlvffit`, `edlvfelv`, `edlvfdlt`, `edlvfeme`, `edlvfenl`, `edlvfeno`, `edlvfgpl`, `edlvfept`, `edlvfdrs`, `edlvfdsk`, `edlvfesi`, `edlvfges`, `edlvfdse`, `edlvfdch`, `edlvfdua`, `edufcgb1`, `edufbgb2`, `edagefgb`, `edlvmeat`, `edlvmebe`, `edlvmebg`, `edlvmehr`, `edlvmgcy`, `edlvmdee`, `edlvmdfi`, `edlvmdfr`, `edlvmegr`, `edlvmdahu`, `edlvmdis`, `edlvmdie`, `edumbil1`, `edumail2`, `edlvmfit`, `edlvmelv`, `edlvmdlt`, `edlvmeme`, `edlvmenl`, `edlvmeno`, `edlvmgpl`, `edlvmept`, `edlvmdrs`, `edlvmdsk`, `edlvmesi`, `edlvmges`, `edlvmdse`, `edlvmdch`, `edlvmdua`, `edumcgb1`, `edumbgb2`, `edagemgb`

## Schritt 5 – Spalten mit > 50% Wert 0 gelöscht

Gelöschte Spalten (127): `dscrrce`, `dscrntn`, `dscrrlg`, `dscrlng`, `dscretn`, `dscrage`, `dscrgnd`, `dscrsex`, `dscrdsb`, `dscroth`, `dscrdk`, `dscrref`, `dscrna`, `dshltnt`, `dshltref`, `dshltdk`, `dshltna`, `medtrnp`, `medtrnt`, `medtroc`, `medtrnl`, `medtrwl`, `medtrnaa`, `medtroth`, `medtrref`, `medtrdk`, `medtrna`, `trhltacu`, `trhltacp`, `trhltcm`, `trhltch`, `trhltos`, `trhltho`, `trhltht`, `trhlthy`, `trhltmt`, `trhltpt`, `trhltre`, `trhltsh`, `trhltref`, `trhltdk`, `trhltna`, `hltprhc`, `hltprhb`, `hltprbp`, `hltpral`, `hltprpa`, `hltprpf`, `hltprsd`, `hltprsc`, `hltprsh`, `hltprdi`, `hltprnt`, `hltprref`, `hltprdk`, `hltprna`, `hltphhc`, `hltphhb`, `hltphbp`, `hltphal`, `hltphbn`, `hltphpa`, `hltphpf`, `hltphsd`, `hltphsc`, `hltphsh`, `hltphdi`, `hltphnt`, `hltphnap`, `hltphref`, `hltphdk`, `hltphna`, `jbexpvi`, `jbexpti`, `jbexpml`, `jbexpmc`, `jbexpnt`, `jbexpnap`, `jbexpref`, `jbexpdk`, `jbexpna`, `jbexevl`, `jbexevh`, `jbexevc`, `jbexera`, `jbexecp`, `jbexebs`, `jbexent`, `jbexenap`, `jbexeref`, `jbexedk`, `jbexena`, `paccmoro`, `paccdwlr`, `pacclift`, `paccnbsh`, `paccocrw`, `paccxhoc`, `paccnois`, `paccinro`, `paccref`, `paccdk`, `paccna`, `edctn`, `uempla`, `uempli`, `dsbld`, `rtrd`, `cmsrv`, `hswrk`, `dngoth`, `dngref`, `dngdk`, `dngna`, `pdwrkp`, `edctnp`, `uemplap`, `uemplip`, `dsbldp`, `rtrdp`, `cmsrvp`, `hswrkp`, `dngothp`, `dngdkp`, `dngnapp`, `dngrefp`, `dngnap`

## Schritt 6 – Missing-Codes durch leere Zellen ersetzt

861 Zellen im Fragebogen, 132515 im Profil

## Schritt 7 – Personen mit ≥ 1 unbeantworteter Frage entfernt

Kriterium: nur die 21 Fragebogen-Items; leere Profil-Zellen bleiben erlaubt

## Schritt 8 – Interview-Metadaten und doppelte Kodierungen gelöscht

Keine inhaltliche Information über die Person, aber Hinweise auf den ESS-Datensatz oder Doppelkodierungen (siehe config.PROFILE_DROP_GROUPS). Gewichte und Stichprobendesign bleiben.

Gelöschte Spalten (35): `name`, `essround`, `edition`, `proddate`, `regunit`, `mode`, `recon`, `inwds`, `ainws`, `ainwe`, `binwe`, `cinwe`, `dinwe`, `einwe`, `finwe`, `hinwe`, `iinwe`, `kinwe`, `rinwe`, `inwde`, `jinws`, `jinwe`, `inwtm`, `nobingnd`, `icgndra`, `yrbrn`, `agegroup`, `edulvlb`, `eisced`, `edulvlpb`, `eiscedp`, `edulvlfb`, `eiscedf`, `edulvlmb`, `eiscedm`
