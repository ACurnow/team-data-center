# Data sources / データの出典

This page lists every value the models use, with its source, or marks it as an assumption. Values were checked on 2026-11-23 unless noted.
モデルで使う数字と、その出典（または仮定）の一覧です。確認日は、特に書いていない限り2026年11月23日です。

## Data centers in Ishikari / 石狩のデータセンター

| Item | Value | Source |
|---|---|---|
| Ishikari Renewable Energy Data Center No. 1: operator | 合同会社石狩再エネデータセンター第1号. Set up by Flower Communications; Tokyu Land and Flower manage the project; Broadband Tower manages the building | https://www.bbtower.co.jp/ir/pr/docs/20251128_ishikari_release.pdf |
| No. 1: location | 石狩市新港中央1丁目722番1 (lot number) | https://prtimes.jp/main/html/rd/p/000000693.000006953.html |
| No. 1: power and size | 15,000 kVA receiving; at least 10 MW from August 2026; 6 halls, 1,140 racks | the source above; https://cloud.watch.impress.co.jp/docs/news/2097920.html |
| No. 1: start of service | 1 August 2026, on 100 % renewable power | https://www.tv-tokyo.co.jp/plus/external-pr/entry/269543.html |
| No. 1: IT load, waste-heat plan | not published | — |
| Sakura Internet Ishikari Data Center: size | 3 buildings, up to about 3,000 racks (2015 plan; the full plan is 5 buildings, about 6,800 racks). Capacity in MW not published | https://www.sakura.ad.jp/corporate/corp/datacenter/ ; https://cloud.watch.impress.co.jp/docs/news/723209.html |
| Sakura: heat reuse in its 2011 design | Server exhaust heat preheats the offices and warms water for snow-melting pipes around the building | https://nikkenren.com/kenchiku/sb/pdf/223/12-024.pdf |
| KCCS ZED Ishikari | Operating since 1 October 2024; 2–3 MW, 400 racks; waste heat used for underfloor heating and road heating | https://cloud.watch.impress.co.jp/docs/news/1627835.html ; https://www.env.go.jp/content/900514282.pdf |
| NTT-ME container data centers (planned) | Up to 14 units of 2 MW (IT load about 1.5 MW each); first unit in April 2027 at the earliest | https://cloud.watch.impress.co.jp/docs/news/2057156.html |

## Prices and costs / 価格と費用

| Item | Value | Source |
|---|---|---|
| Kerosene, Hokkaido, survey of 16 November 2026 | 156.8 yen/L at the station; 160.1 yen/L delivered. National averages: 144.2 and 154.9 yen/L | https://www.enecho.meti.go.jp/statistics/petroleum_and_lpgas/pl007/xlsx/261118.xlsx |
| Kerosene, conservative value used in the model | 115 yen/L | Assumption: bulk buyers pay less than the 18 L retail price |
| Pre-insulated two-pipe heat network: direct cost per metre of route (2019 quotes) | Steel 25A–250A about 40,000–250,000 yen/m; plastic about 20,000–150,000 yen/m; overhead adds about 33 % | https://ynu.repo.nii.ac.jp/record/12712/files/tachibana_masaya-thesis.pdf (values read from charts) |

## Prototype model parameters (theme 1) / 試作モデルのパラメータ（テーマ1）

| Parameter | Value | Source or assumption |
|---|---|---|
| IT load of one data center | 10 MW | Assumption |
| Recoverable share of IT heat at 30–35 °C | 0.6 | Assumption |
| Heat-pump COP (to about 60 °C) | 4.0 | Assumption |
| Boiler efficiency (kerosene) | 0.85 | Assumption |
| Lower heating value of kerosene | 9.7 kWh/L | Assumption (standard value) |
| CO2 from kerosene | 2.49 kg/L | Ministry of the Environment emission factor (URL to be added) |
| Heat-pump electricity | 25 yen/kWh | Assumption |
| Pipe, installed, both directions | 100,000 yen per metre of street | Assumption; compare with the range above |
| Annuity | 3 %, 30 years | Assumption |
| Heated greenhouse demand in Hokkaido | 0.40 MWh/m² per year | Assumption |
| Snow melting | 0.12 MWh/m² per year | Assumption: about 0.25 kWh/m² per cm of snowfall × 479 cm |

## Climate / 気象

| Item | Source |
|---|---|
| Monthly mean temperature and snowfall, Sapporo (station 47412), normals 1991–2020 | JMA: https://www.data.jma.go.jp/obd/stats/etrn/view/nml_sfc_ym.php?prec_no=14&block_no=47412 |

## Precedents / 先行事例

| Case | Source |
|---|---|
| White Data Center, Bibai: server heat warms snowmelt water to 25–28 °C for eel farming (since January 2024) | https://www.hokkaido-np.co.jp/movies/detail/6357590939112/ |
| Hokkaido University: recovering half of a supercomputer's heat gives 6–8 MWh/day, about the heating of 60–80 homes | https://hu-gxc.eng.hokudai.ac.jp/wp-content/uploads/2026/03/gxc2025_excellence_16-osawa.pdf |

## Model v2 parameters (theme 1) / 改良版モデルのパラメータ（テーマ1）

Generated from `dcopt.heat.network.assumptions_table(Params())`. Values with two entries are ambient / central mode, or low / high case.
`dcopt.heat.network.assumptions_table(Params())` から作成。値が2つあるものは、低温方式／集中方式、または低い場合／高い場合です。

| Item | 項目 | Value | Unit | Basis |
|---|---|---|---|---|
| Recoverable share of IT heat | 回収できる廃熱の割合 | 0.6 |  | assumption (as v1): 30-35 C capture |
| Waste-heat temperature | 廃熱の温度 | 30.0 | C | assumption: liquid or rear-door cooling |
| Ambient loop temperature | 低温導管網の温度 | 30.0 | C | assumption |
| Central network supply | 集中方式の送り温度 | 60.0 | C | assumption: enough for hot water |
| Share of Carnot COP | カルノー効率に対する割合 | 0.5 |  | assumption: 45-55 % typical |
| COP cap | COPの上限 | 8.0 |  | assumption: manufacturer range for small lifts |
| Supply-return difference | 往き還りの温度差 | 10 / 30 | K | assumption: ambient / central |
| Network heat loss | 導管の熱損失 | 2% / 8% |  | assumption: ambient / central |
| Kerosene price | 灯油価格 | 115 / 156.8 | yen/L | assumption (conservative bulk) / source: ANRE survey 2026-11-16, Hokkaido (https://www.enecho.meti.go.jp/statistics/petroleum_and_lpgas/pl007/xlsx/261118.xlsx) |
| Boiler efficiency replaced | 置き換えるボイラーの効率 | 0.85 |  | assumption (as v1) |
| Electricity price | 電気代 | 25.0 | yen/kWh | assumption (as v1) |
| Kerosene CO2 factor | 灯油のCO2排出係数 | 2.49 | kg/L | source: https://ghg-santeikohyo.env.go.jp/calc |
| Grid electricity CO2 | 系統電力のCO2 | 0.55 | t/MWh | assumption (as v1) |
| Pipe life, discount rate | 導管の年数・割引率 | 30 / 3% |  | assumption (as v1) |
| Heat-pump life | ヒートポンプの年数 | 20 | years | assumption |
| Heat-pump investment | ヒートポンプの投資 | 0 / 0 | yen/MW | user / central; off by default (to verify with makers) |
| Sized share of each user's peak | 管とヒートポンプの容量（ピーク比） | 1.0 |  | assumption |
| Peak factors | ピーク係数 | greenhouse 2.5, new_greenhouse 2.5, aquaculture 1.2, snow 3, pool 1.4, onsen 1.4, hospital 1.8, school 2 |  | assumption: greenhouses heat mostly at night (2.5); snow melting follows snowfall events (3.0); space heating 1.8-2.0; pools and baths are steady (1.4); fish farms very steady (1.2) |
| Pipe cost per metre | 導管の単価 | DN50 84,233, DN80 121,473, DN100 146,300, DN150 208,367, DN200 270,433, DN250 332,500 | yen/m | assumption: straight line through the 2019 quotes for small two-pipe pre-insulated steel networks (25A about 40,000, 250A about 250,000 yen per metre of route, direct cost) plus about 33 % overhead, read off the charts in https://ynu.repo.nii.ac.jp/record/12712/files/tachibana_masaya-thesis.pdf |
| Pipe capacity | 導管の容量 | DN50 0.09, DN80 0.25, DN100 0.54, DN150 1.41, DN200 2.72, DN250 4.62 | MW | water 990 kg/m3, 4.18 kJ/kgK, dT 10 K, velocities 1, 1.2, 1.5, 1.8, 2, 2.2 m/s (assumption), JIS G 3452 inner diameters |
| Supply temperature: Greenhouses (existing) | 必要温度：温室（既存） | 45.0 | C | assumption: hot-water pipe heating in greenhouses runs at about 40-50 C |
| Supply temperature: New greenhouse site (assumed) | 必要温度：温室の新設候補（仮定） | 45.0 | C | assumption: as existing greenhouses |
| Supply temperature: Land-based fish farm (assumed) | 必要温度：陸上養殖（仮定） | 22.0 | C | assumption: rearing water 15-28 C by species (eel 25-28 C in the Bibai case); 22 C as a middle value |
| Supply temperature: Snow melting (assumed) | 必要温度：ロードヒーティング（仮定） | 25.0 | C | assumption: low-temperature hydronic snow melting can run on 20-30 C water |
| Supply temperature: Pool / sports centre | 必要温度：プール・運動施設 | 40.0 | C | assumption: pool water about 28-30 C plus hall heating about 40 C |
| Supply temperature: Hot spring / bath | 必要温度：温泉・浴場 | 60.0 | C | assumption: hot water stored at 60 C or more against Legionella |
| Supply temperature: Hospital | 必要温度：病院 | 60.0 | C | assumption: hot water at 60 C or more; space heating 45-60 C |
| Supply temperature: School | 必要温度：学校 | 45.0 | C | assumption: low-temperature radiators or floor heating about 45 C |
