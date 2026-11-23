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
