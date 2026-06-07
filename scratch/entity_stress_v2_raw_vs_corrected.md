# Entity Stress v2: Raw N-ATLaS vs Correction Layer

Summary:
- Samples: 86
- Raw entity preservation: 0.3236
- Corrected entity preservation: 0.8304
- Lift: 0.5068
- Avg correction latency: 6.3439 ms

## S001 - provider_bank_status_support

Audio: ``
Expected entities: OPay, Access Bank, pending, reversal
Raw score: 0.2500
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
mo lo pe lati ran owo si access bank ṣugun transcional wa ni pẹndin, mo fẹri faṣa o
```
Correction layer output:
```text
OPay lati ran owo si Access Bank Bank sugun transcional wa ni pending mo reversal o
```
Corrections applied:
- `access bank` -> `Access Bank` (bank)
- `feri fasa` -> `reversal` (support_term)
- `mo lo pe` -> `OPay` (provider)
- `reversal` -> `reversal` (support_term)
- `access` -> `Access Bank` (bank)
- `pendin` -> `pending` (status)
- `opay` -> `OPay` (provider)
Remaining missing entities: none

## S002 - provider_bank_status_support

Audio: ``
Expected entities: PalmPay, Fidelity Bank, successful, failed transfer
Raw score: 0.2500
Corrected score: 0.7500

Raw N-ATLaS transcript:
```text
mo lo pampé láti rán owó sí fidelity bank, ṣùgbọ́n transcation náà wà ní suxsessful, mo fẹ́ fẹ́ ó tránsfà
```
Correction layer output:
```text
mo lo PalmPay lati ran owo si Fidelity Bank Bank sugbon transcation naa wa ni successful mo fe fe o transfa
```
Corrections applied:
- `fidelity bank` -> `Fidelity Bank` (bank)
- `suxsessful` -> `successful` (status)
- `fidelity` -> `Fidelity Bank` (bank)
- `pampe` -> `PalmPay` (provider)
Remaining missing entities: failed transfer

## S003 - provider_bank_status_support

Audio: ``
Expected entities: Moniepoint, FCMB, timeout, chargeback
Raw score: 0.2500
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
mo lo money point lati ran owo si fcmb, ṣugbọn transcion naa wa ni thyme out, mo fẹ charge back
```
Correction layer output:
```text
mo lo Moniepoint lati ran owo si FCMB sugbon transcion naa wa ni timeout mo fe chargeback
```
Corrections applied:
- `money point` -> `Moniepoint` (provider)
- `charge back` -> `chargeback` (support_term)
- `moniepoint` -> `Moniepoint` (provider)
- `chargeback` -> `chargeback` (support_term)
- `thyme out` -> `timeout` (status)
- `timeout` -> `timeout` (status)
- `fcmb` -> `FCMB` (bank)
Remaining missing entities: none

## S004 - provider_bank_status_support

Audio: ``
Expected entities: Kuda, First Bank, pending, dispute
Raw score: 0.5000
Corrected score: 0.7500

Raw N-ATLaS transcript:
```text
mo lókúdá láti rán owó sí first bank, ṣùgbọ́n, tànàsáàṣàn náà wà ní pẹ́ndìn, mo fẹ́ dísípírì
```
Correction layer output:
```text
mo lokuda lati ran owo si First Bank sugbon tanasaasan naa wa ni pending mo fe disipiri
```
Corrections applied:
- `first bank` -> `First Bank` (bank)
- `pendin` -> `pending` (status)
Remaining missing entities: dispute

## S005 - provider_bank_status_support

Audio: ``
Expected entities: Paga, GTBank, successful, transaction history
Raw score: 0.2500
Corrected score: 0.7500

Raw N-ATLaS transcript:
```text
mo lo paga lati ran owó sí gt bank, ṣùgbọ́n transdẹ́ẹ̀ṣàn náà wà ní sọ̀sẹ̀sífọ̀, mo fẹ́ transdẹ́ẹ̀ṣàn history food stop.
```
Correction layer output:
```text
mo lo Paga lati ran owo si GTBank sugbon transdeesan naa wa ni successful mo fe transdeesan history food stop
```
Corrections applied:
- `sosesifo` -> `successful` (status)
- `gt bank` -> `GTBank` (bank)
- `gtbank` -> `GTBank` (bank)
- `paga` -> `Paga` (provider)
Remaining missing entities: transaction history

## S006 - provider_bank_status_support

Audio: ``
Expected entities: Pocket, UBA, timeout, customer care
Raw score: 0.2500
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
mo lo pókẹ́tì láti rán owó sí uba, ṣùgbọ́n tí rán ṣàǹsàn náà wà ní thyme-out, mo fẹ́ custom-made.
```
Correction layer output:
```text
mo lo Pocket lati ran owo si UBA sugbon ti ran sansan naa wa ni timeout mo fe customer care
```
Corrections applied:
- `custom made` -> `customer care` (support_term)
- `thyme out` -> `timeout` (status)
- `timeout` -> `timeout` (status)
- `poketi` -> `Pocket` (provider)
- `uba` -> `UBA` (bank)
Remaining missing entities: none

## S007 - provider_bank_status_support

Audio: ``
Expected entities: NowNow, Zenith Bank, pending, bot
Raw score: 0.2500
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
mo lo náà náà ò̩láti ran owó si zenith bank, ṣùgbó̩n transcirnó̩ wà ní pẹ́ndin, mo fé̩ bò̩ò̩t
```
Correction layer output:
```text
mo lo NowNow olati ran owo si Zenith Bank Bank sugbon transcirno wa ni pending mo fe bot
```
Corrections applied:
- `zenith bank` -> `Zenith Bank` (bank)
- `naa naa` -> `NowNow` (provider)
- `nownow` -> `NowNow` (provider)
- `zenith` -> `Zenith Bank` (bank)
- `pendin` -> `pending` (status)
- `boot` -> `bot` (support_term)
- `bot` -> `bot` (support_term)
Remaining missing entities: none

## S008 - provider_bank_status_support

Audio: ``
Expected entities: KongaPay, Citibank, successful, reversal
Raw score: 0.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
mo lo konga pe lati ran owó sí city bank, ṣùgbọ́n transcation náà wà ní suxsẹsúfù, mo fẹ́rii vásáò
```
Correction layer output:
```text
mo lo KongaPay lati ran owo si Citibank sugbon transcation naa wa ni successful mo reversal
```
Corrections applied:
- `ferii vasao` -> `reversal` (support_term)
- `city bank` -> `Citibank` (bank)
- `suxsesufu` -> `successful` (status)
- `konga pe` -> `KongaPay` (provider)
- `citibank` -> `Citibank` (bank)
- `reversal` -> `reversal` (support_term)
Remaining missing entities: none

## S009 - provider_bank_status_support

Audio: ``
Expected entities: FETS, Ecobank, timeout, failed transfer
Raw score: 0.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
mo lo fí tí s láti rún owó sí èkó báńkì ṣùgbọ́n transcation náà wà ní thyme-out, mo fẹ́ fí ó tírànfà.
```
Correction layer output:
```text
mo lo FETS lati run owo si Ecobank sugbon transcation naa wa ni timeout mo fe failed transfer
```
Corrections applied:
- `fi o tiranfa` -> `failed transfer` (support_term)
- `eko banki` -> `Ecobank` (bank)
- `thyme out` -> `timeout` (status)
- `fi ti s` -> `FETS` (provider)
- `ecobank` -> `Ecobank` (bank)
- `timeout` -> `timeout` (status)
- `fets` -> `FETS` (provider)
Remaining missing entities: none

## S010 - provider_bank_status_support

Audio: ``
Expected entities: Teasy Mobile, Globus Bank, pending, chargeback
Raw score: 0.2500
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
mo lo tí sí móbà láti ran owó sí globus bank, ṣùgbọ́n transcation náà wà ní pẹ́ndìn, mo fẹ́ charge bank.
```
Correction layer output:
```text
mo lo Teasy Mobile Mobile lati ran owo si Globus Bank Bank sugbon transcation naa wa ni pending mo fe chargeback
```
Corrections applied:
- `globus bank` -> `Globus Bank` (bank)
- `charge bank` -> `chargeback` (support_term)
- `ti si moba` -> `Teasy Mobile` (provider)
- `chargeback` -> `chargeback` (support_term)
- `globus` -> `Globus Bank` (bank)
- `pendin` -> `pending` (status)
- `teasy` -> `Teasy Mobile` (provider)
Remaining missing entities: none

## S011 - provider_bank_status_support

Audio: ``
Expected entities: Xpress Wallet, Keystone Bank, successful, dispute
Raw score: 0.5000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
mo lo express wallet lati ran owo si keystone bank, shugbon, transaction naa wa ni suxsessful, mo fẹ disput
```
Correction layer output:
```text
mo lo Xpress wallet balance wallet balance lati ran owo si Keystone Bank Bank shugbon transaction naa wa ni successful mo fe dispute
```
Corrections applied:
- `express wallet` -> `Xpress Wallet` (provider)
- `xpress wallet` -> `Xpress Wallet` (provider)
- `keystone bank` -> `Keystone Bank` (bank)
- `suxsessful` -> `successful` (status)
- `keystone` -> `Keystone Bank` (bank)
- `xpress` -> `Xpress Wallet` (provider)
- `disput` -> `dispute` (support_term)
- `wallet` -> `wallet balance` (account_term)
Remaining missing entities: none

## S012 - provider_bank_status_support

Audio: ``
Expected entities: Chams Mobile, Polaris Bank, timeout, transaction history
Raw score: 0.2500
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
mo lo chimes mo bao lati ran owo si po karis bank, ṣugbọn transaction naa wa ni thyme out, mo fẹ́ transaction history.
```
Correction layer output:
```text
mo lo Chams Mobile Mobile lati ran owo si Polaris Bank Bank sugbon transaction naa wa ni timeout mo fe transaction history
```
Corrections applied:
- `transaction history` -> `transaction history` (support_term)
- `chimes mo bao` -> `Chams Mobile` (provider)
- `po karis bank` -> `Polaris Bank` (bank)
- `chams mobile` -> `Chams Mobile` (provider)
- `polaris bank` -> `Polaris Bank` (bank)
- `thyme out` -> `timeout` (status)
- `polaris` -> `Polaris Bank` (bank)
- `timeout` -> `timeout` (status)
- `chams` -> `Chams Mobile` (provider)
Remaining missing entities: none

## S013 - provider_bank_status_support

Audio: ``
Expected entities: Mkudi, Stanbic IBTC, pending, customer care
Raw score: 0.0000
Corrected score: 0.7500

Raw N-ATLaS transcript:
```text
láti rán owó sí stímbìk, iptc, ṣùgbọ́n, tàǹsáńsù náà wà ní pẹ́ndín, mo fẹ́ kọ́stọ́mákìẹ̀.
```
Correction layer output:
```text
lati ran owo si Mkudi sugbon tansansu naa wa ni pending mo fe customer care
```
Corrections applied:
- `stimbik iptc` -> `Mkudi` (provider)
- `kostomakie` -> `customer care` (support_term)
- `pendin` -> `pending` (status)
- `mkudi` -> `Mkudi` (provider)
Remaining missing entities: Stanbic IBTC

## S014 - provider_bank_status_support

Audio: ``
Expected entities: Parkway, Standard Chartered, successful, bot
Raw score: 0.5000
Corrected score: 0.7500

Raw N-ATLaS transcript:
```text
mo lo parkway lati ran owo si standard chart aded, ṣugbon transaction naa wa ni suxsessful, mo fẹ bọt
```
Correction layer output:
```text
mo lo Parkway lati ran owo si standard chart aded sugbon transaction naa wa ni successful mo fe bot
```
Corrections applied:
- `suxsessful` -> `successful` (status)
- `parkway` -> `Parkway` (provider)
- `bot` -> `bot` (support_term)
Remaining missing entities: Standard Chartered

## S015 - provider_bank_status_support

Audio: ``
Expected entities: MoMo PSB, Sterling Bank, timeout, reversal
Raw score: 0.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
mo lo mo mú pshb láti ran owó sí stírímbánk, ṣùgbọ́n, tẹ̀ránṣọ́nà wà ní taímáàòtù mo fẹ́ ríi báṣà ọ
```
Correction layer output:
```text
mo lo MoMo PSB PSB lati ran owo si Sterling Bank Bank sugbon teransona wa ni timeout mo fe reversal o
```
Corrections applied:
- `mo mu pshb` -> `MoMo PSB` (provider)
- `stirimbank` -> `Sterling Bank` (bank)
- `taimaaotu` -> `timeout` (status)
- `momo psb` -> `MoMo PSB` (provider)
- `sterling` -> `Sterling Bank` (bank)
- `rii basa` -> `reversal` (support_term)
- `timeout` -> `timeout` (status)
- `momo` -> `MoMo PSB` (provider)
Remaining missing entities: none

## S016 - provider_bank_status_support

Audio: ``
Expected entities: SmartCash PSB, Titan Trust Bank, pending, failed transfer
Raw score: 0.2500
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
mo lo smart cash, psb lati ran owó sí titan trust bank, ṣùgbọ́n transactions náà wà ní pẹndin, mo fẹ́ field transport.
```
Correction layer output:
```text
mo lo SmartCash PSB PSB psb lati ran owo si Titan Trust Bank Bank sugbon transactions naa wa ni pending mo fe failed transfer
```
Corrections applied:
- `titan trust bank` -> `Titan Trust Bank` (bank)
- `field transport` -> `failed transfer` (support_term)
- `titan trust` -> `Titan Trust Bank` (bank)
- `smart cash` -> `SmartCash PSB` (provider)
- `smartcash` -> `SmartCash PSB` (provider)
- `pendin` -> `pending` (status)
Remaining missing entities: none

## S017 - provider_bank_status_support

Audio: ``
Expected entities: MoneyMaster PSB, Union Bank, successful, chargeback
Raw score: 0.5000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
mo ló mọ́ ní mástà psb láti rán owó sí union bank, ṣùgbó ń trànsáà náà wà ní sọ̀sẹ́fọ̀ mọ́ fẹ́ chargeback.
```
Correction layer output:
```text
mo lo MoneyMaster PSB PSB lati ran owo si Union Bank Bank sugbo n transaa naa wa ni successful mo fe chargeback
```
Corrections applied:
- `mo ni masta psb` -> `MoneyMaster PSB` (provider)
- `moneymaster` -> `MoneyMaster PSB` (provider)
- `union bank` -> `Union Bank` (bank)
- `chargeback` -> `chargeback` (support_term)
- `sosefo` -> `successful` (status)
- `union` -> `Union Bank` (bank)
Remaining missing entities: none

## S018 - provider_bank_status_support

Audio: ``
Expected entities: 9PSB, Unity Bank, timeout, dispute
Raw score: 0.2500
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
mo ló ní p.s.b. láti rán owó sí unity bank, ṣùgbọ́n, tànàṣẹ́n náà wà ní time-out, mo fẹ́ díspíò
```
Correction layer output:
```text
mo lo 9PSB lati ran owo si Unity Bank Bank sugbon tanasen naa wa ni timeout mo fe dispute
```
Corrections applied:
- `unity bank` -> `Unity Bank` (bank)
- `ni p s b` -> `9PSB` (provider)
- `time out` -> `timeout` (status)
- `timeout` -> `timeout` (status)
- `dispio` -> `dispute` (support_term)
- `unity` -> `Unity Bank` (bank)
- `9psb` -> `9PSB` (provider)
Remaining missing entities: none

## S019 - provider_bank_status_support

Audio: ``
Expected entities: Nomba, Wema Bank, pending, transaction history
Raw score: 0.5000
Corrected score: 0.7500

Raw N-ATLaS transcript:
```text
mo lo nọ́ḿbà láti ran òwòsí wema bank, ṣùgbọ́n transcion náà wà ní pẹ́ndín, mo fẹ́ transcionístrí.
```
Correction layer output:
```text
mo lo Nomba lati ran owosi Wema Bank Bank sugbon transcion naa wa ni pending mo fe transcionistri
```
Corrections applied:
- `wema bank` -> `Wema Bank` (bank)
- `pendin` -> `pending` (status)
- `nomba` -> `Nomba` (provider)
- `wema` -> `Wema Bank` (bank)
Remaining missing entities: transaction history

## S020 - bank_pair_reference_receipt

Audio: ``
Expected entities: Premium Trust Bank, Optimus Bank, transaction reference, receipt
Raw score: 1.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
transfer lati premium trust bank si optimus bank ni transaction reference ṣugbon ko si receipt
```
Correction layer output:
```text
transfer lati Premium Trust Bank Bank si Optimus Bank Bank ni transaction reference sugbon ko si receipt
```
Corrections applied:
- `transaction reference` -> `transaction reference` (transaction_term)
- `premium trust bank` -> `Premium Trust Bank` (bank)
- `premium trust` -> `Premium Trust Bank` (bank)
- `optimus bank` -> `Optimus Bank` (bank)
- `optimus` -> `Optimus Bank` (bank)
- `receipt` -> `receipt` (transaction_term)
Remaining missing entities: none

## S021 - bank_pair_reference_receipt

Audio: ``
Expected entities: Providus Bank, Parallex Bank, transaction reference, receipt
Raw score: 0.7500
Corrected score: 0.7500

Raw N-ATLaS transcript:
```text
transfer latí providus bank sí parlance bank ní transaction reference ṣùgbọ́n kò sí receipt.
```
Correction layer output:
```text
transfer lati Providus Bank Bank si parlance bank ni transaction reference sugbon ko si receipt
```
Corrections applied:
- `transaction reference` -> `transaction reference` (transaction_term)
- `providus bank` -> `Providus Bank` (bank)
- `providus` -> `Providus Bank` (bank)
- `receipt` -> `receipt` (transaction_term)
Remaining missing entities: Parallex Bank

## S022 - bank_pair_reference_receipt

Audio: ``
Expected entities: SunTrust Bank, Signature Bank, transaction reference, receipt
Raw score: 0.5000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
transfer lati sunkrothed bank, c-signature bank, ni transaction rẹfẹrin ṣugbọn ko si receipt.
```
Correction layer output:
```text
transfer lati SunTrust Bank Bank c Signature Bank Bank ni transaction reference sugbon ko si receipt
```
Corrections applied:
- `transaction referin` -> `transaction reference` (transaction_term)
- `sunkrothed bank` -> `SunTrust Bank` (bank)
- `signature bank` -> `Signature Bank` (bank)
- `suntrust bank` -> `SunTrust Bank` (bank)
- `signature` -> `Signature Bank` (bank)
- `suntrust` -> `SunTrust Bank` (bank)
- `receipt` -> `receipt` (transaction_term)
Remaining missing entities: none

## S023 - bank_pair_reference_receipt

Audio: ``
Expected entities: Jaiz Bank, TAJ Bank, transaction reference, receipt
Raw score: 0.0000
Corrected score: 0.7500

Raw N-ATLaS transcript:
```text
transfalà láti jáìsì báǹk sí tí ájé báǹk ní táǹsás̩áń rè̩rè̩ǹs̩, s̩ùgbò̩n kò sírís̩ìtì
```
Correction layer output:
```text
transfala lati jaisi bank si TAJ Bank Bank ni transaction reference sugbon ko receipt
```
Corrections applied:
- `tansasan rerens` -> `transaction reference` (transaction_term)
- `ti aje bank` -> `TAJ Bank` (bank)
- `taj bank` -> `TAJ Bank` (bank)
- `sirisiti` -> `receipt` (transaction_term)
- `receipt` -> `receipt` (transaction_term)
- `taj` -> `TAJ Bank` (bank)
Remaining missing entities: Jaiz Bank

## S024 - bank_pair_reference_receipt

Audio: ``
Expected entities: Lotus Bank, Alternative Bank, transaction reference, receipt
Raw score: 0.7500
Corrected score: 0.7500

Raw N-ATLaS transcript:
```text
transfer lati lotus bank si alternative bank ni transassional reference ṣugbon ko si receipt
```
Correction layer output:
```text
transfer lati Lotus Bank Bank si Alternative Bank Bank ni transassional reference sugbon ko si receipt
```
Corrections applied:
- `alternative bank` -> `Alternative Bank` (bank)
- `alternative` -> `Alternative Bank` (bank)
- `lotus bank` -> `Lotus Bank` (bank)
- `receipt` -> `receipt` (transaction_term)
- `lotus` -> `Lotus Bank` (bank)
Remaining missing entities: transaction reference

## S025 - digital_bank_account_term

Audio: ``
Expected entities: Carbon, wallet balance, Access Bank
Raw score: 0.0000
Corrected score: 0.6667

Raw N-ATLaS transcript:
```text
karbonar mi sọ pé wallet balans lori transfers bank access
```
Correction layer output:
```text
karbonar mi so pe wallet balance wallet balance balance lori transfers bank Access Bank
```
Corrections applied:
- `wallet balans` -> `wallet balance` (account_term)
- `balance` -> `wallet balance` (account_term)
- `access` -> `Access Bank` (bank)
- `wallet` -> `wallet balance` (account_term)
Remaining missing entities: Carbon

## S026 - digital_bank_account_term

Audio: ``
Expected entities: FairMoney, account restricted, Fidelity Bank
Raw score: 0.6667
Corrected score: 0.6667

Raw N-ATLaS transcript:
```text
femony ap mi sọ pe account restricted lori transfers si fidelity bank.
```
Correction layer output:
```text
femony ap mi so pe account restricted lori transfers si Fidelity Bank Bank
```
Corrections applied:
- `account restricted` -> `account restricted` (account_term)
- `fidelity bank` -> `Fidelity Bank` (bank)
- `fidelity` -> `Fidelity Bank` (bank)
Remaining missing entities: FairMoney

## S027 - digital_bank_account_term

Audio: ``
Expected entities: ALAT, daily limit, FCMB
Raw score: 0.6667
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
alatap mi sọ pé daylilimit lori transfa si fcmb
```
Correction layer output:
```text
alatap mi so pe daily limit lori transfa si FCMB
```
Corrections applied:
- `daylilimit` -> `daily limit` (account_term)
- `fcmb` -> `FCMB` (bank)
Remaining missing entities: none

## S028 - digital_bank_account_term

Audio: ``
Expected entities: VBank, wallet balance, First Bank
Raw score: 0.6667
Corrected score: 0.6667

Raw N-ATLaS transcript:
```text
the bank ap mi sọ pe wallet balance lori transfers si first bank
```
Correction layer output:
```text
the bank ap mi so pe wallet balance wallet balance balance lori transfers si First Bank
```
Corrections applied:
- `wallet balance` -> `wallet balance` (account_term)
- `first bank` -> `First Bank` (bank)
- `balance` -> `wallet balance` (account_term)
- `wallet` -> `wallet balance` (account_term)
Remaining missing entities: VBank

## S029 - digital_bank_account_term

Audio: ``
Expected entities: Eyowo, account restricted, GTBank
Raw score: 0.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
iyowo àpamí sọ pé àkọọ̀ntì stricte lórí transciti gt bank.
```
Correction layer output:
```text
Eyowo apami so pe account restricted lori transciti GTBank
```
Corrections applied:
- `akoonti stricte` -> `account restricted` (account_term)
- `gt bank` -> `GTBank` (bank)
- `gtbank` -> `GTBank` (bank)
- `iyowo` -> `Eyowo` (digital_bank)
Remaining missing entities: none

## S030 - digital_bank_account_term

Audio: ``
Expected entities: Carbon, daily limit, UBA
Raw score: 0.6667
Corrected score: 0.6667

Raw N-ATLaS transcript:
```text
carbon àpì mi sọ pé daylìlìmí ti lórí transcene uba.
```
Correction layer output:
```text
Carbon api mi so pe daylilimi ti lori transcene UBA
```
Corrections applied:
- `carbon` -> `Carbon` (digital_bank)
- `uba` -> `UBA` (bank)
Remaining missing entities: daily limit

## S031 - digital_bank_account_term

Audio: ``
Expected entities: FairMoney, wallet balance, Zenith Bank
Raw score: 0.3333
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
fẹ́mọ́ní apì mi sọ pé wálẹ̀t baláǹs̀ lórí, táǹṣfà sí zenith bank.
```
Correction layer output:
```text
FairMoney api mi so pe wallet balance wallet balance balance lori tansfa si Zenith Bank Bank
```
Corrections applied:
- `walet balans` -> `wallet balance` (account_term)
- `zenith bank` -> `Zenith Bank` (bank)
- `balance` -> `wallet balance` (account_term)
- `femoni` -> `FairMoney` (digital_bank)
- `zenith` -> `Zenith Bank` (bank)
- `wallet` -> `wallet balance` (account_term)
Remaining missing entities: none

## S032 - digital_bank_account_term

Audio: ``
Expected entities: ALAT, account restricted, Citibank
Raw score: 0.6667
Corrected score: 0.6667

Raw N-ATLaS transcript:
```text
alatap mi sọ pe account restricted lori transfaasi citybank
```
Correction layer output:
```text
alatap mi so pe account restricted lori transfaasi citybank
```
Corrections applied:
- `account restricted` -> `account restricted` (account_term)
Remaining missing entities: Citibank

## S033 - digital_bank_account_term

Audio: ``
Expected entities: VBank, daily limit, Ecobank
Raw score: 0.3333
Corrected score: 0.6667

Raw N-ATLaS transcript:
```text
fi banka pín sọ pé day lily meat lori transcensivá sí ecobank
```
Correction layer output:
```text
fi banka PIN so pe daily limit lori transcensiva si Ecobank
```
Corrections applied:
- `day lily meat` -> `daily limit` (account_term)
- `daily limit` -> `daily limit` (account_term)
- `ecobank` -> `Ecobank` (bank)
- `pin` -> `PIN` (security_term)
Remaining missing entities: VBank

## S034 - digital_bank_account_term

Audio: ``
Expected entities: Eyowo, wallet balance, Globus Bank
Raw score: 0.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
ẹ̀yọ̀ áàpù mi sọ pé wálẹ̀t balans lórí tránsfásì gúlóbòs bánkì
```
Correction layer output:
```text
Eyowo mi so pe wallet balance wallet balance balance lori transfasi Globus Bank Bank
```
Corrections applied:
- `gulobos banki` -> `Globus Bank` (bank)
- `walet balans` -> `wallet balance` (account_term)
- `globus bank` -> `Globus Bank` (bank)
- `eyo aapu` -> `Eyowo` (digital_bank)
- `balance` -> `wallet balance` (account_term)
- `globus` -> `Globus Bank` (bank)
- `wallet` -> `wallet balance` (account_term)
- `eyowo` -> `Eyowo` (digital_bank)
Remaining missing entities: none

## S035 - processor_card_payment_term

Audio: ``
Expected entities: Paystack, Verve, debit card
Raw score: 0.3333
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
pestac payment lori veff card ni debit card, mo nilo hẹnpẹ.
```
Correction layer output:
```text
Paystack payment lori Verve ni debit card mo nilo henpe
```
Corrections applied:
- `debit card` -> `debit card` (payment_term)
- `veff card` -> `Verve` (card_scheme)
- `pestac` -> `Paystack` (payment_processor)
- `verve` -> `Verve` (card_scheme)
- `debit` -> `debit` (payment_term)
Remaining missing entities: none

## S036 - processor_card_payment_term

Audio: ``
Expected entities: Flutterwave, Visa, virtual card
Raw score: 0.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
flotterway payment lori fisicard ni bachelocard mo nilo help.
```
Correction layer output:
```text
Flutterwave payment lori Visa ni virtual card mo nilo help
```
Corrections applied:
- `bachelocard` -> `virtual card` (payment_term)
- `flotterway` -> `Flutterwave` (payment_processor)
- `fisicard` -> `Visa` (card_scheme)
- `visa` -> `Visa` (card_scheme)
Remaining missing entities: none

## S037 - processor_card_payment_term

Audio: ``
Expected entities: Interswitch, Mastercard, debit
Raw score: 0.3333
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
ìtà̀sùlítì pẹ́mẹ̀tì lórí masakadkadì ní débìtì mu nílò hẹ́ọ̀pù
```
Correction layer output:
```text
Interswitch pemeti lori Mastercard ni debit mu nilo heopu
```
Corrections applied:
- `masakadkadi` -> `Mastercard` (card_scheme)
- `mastercard` -> `Mastercard` (card_scheme)
- `itasuliti` -> `Interswitch` (payment_processor)
- `debiti` -> `debit` (payment_term)
- `debit` -> `debit` (payment_term)
Remaining missing entities: none

## S038 - processor_card_payment_term

Audio: ``
Expected entities: Remita, Verve, credit
Raw score: 0.6667
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
remita payment lórí waafkard ni credit mo nílò help
```
Correction layer output:
```text
Remita lori Verve ni credit mo nilo help
```
Corrections applied:
- `remita payment` -> `Remita` (payment_processor)
- `waafkard` -> `Verve` (card_scheme)
- `remita` -> `Remita` (payment_processor)
- `credit` -> `credit` (payment_term)
- `verve` -> `Verve` (card_scheme)
Remaining missing entities: none

## S039 - channel_customer_care

Audio: ``
Expected entities: USSD, Paga, customer care, bot
Raw score: 0.2500
Corrected score: 0.7500

Raw N-ATLaS transcript:
```text
usd lori paga ko ṣiṣẹ, kọsitọmá kẹbọd kò rán mi lọ́wọ́
```
Correction layer output:
```text
USSD lori Paga ko sise kositoma bot ko ran mi lowo
```
Corrections applied:
- `kebod` -> `bot` (support_term)
- `paga` -> `Paga` (provider)
- `usd` -> `USSD` (channel)
- `bot` -> `bot` (support_term)
Remaining missing entities: customer care

## S040 - channel_customer_care

Audio: ``
Expected entities: ATM, Pocket, customer care, bot
Raw score: 0.2500
Corrected score: 0.7500

Raw N-ATLaS transcript:
```text
atm lórí pọ́kẹ̀tì kò ṣiṣẹ́ kọ́stọ́má kẹ́bọd kò rán mi lọ́wọ́
```
Correction layer output:
```text
ATM lori Pocket ko sise customer care ko ran mi lowo
```
Corrections applied:
- `kostoma kebod` -> `customer care` (support_term)
- `poketi` -> `Pocket` (provider)
- `atm` -> `ATM` (channel)
Remaining missing entities: bot

## S041 - channel_customer_care

Audio: ``
Expected entities: POS, NowNow, customer care, bot
Raw score: 0.5000
Corrected score: 0.7500

Raw N-ATLaS transcript:
```text
pọ́ṣ lórí náà náà kò ṣiṣẹ́, kọ́́sínmá kẹ́bọ́t kò omi lọ́wọ́
```
Correction layer output:
```text
POS lori NowNow ko sise kosinma kebot ko omi lowo
```
Corrections applied:
- `naa naa` -> `NowNow` (provider)
- `nownow` -> `NowNow` (provider)
- `pos` -> `POS` (channel)
Remaining missing entities: customer care

## S042 - channel_customer_care

Audio: ``
Expected entities: QR Code, KongaPay, customer care, bot
Raw score: 0.2500
Corrected score: 0.5000

Raw N-ATLaS transcript:
```text
kiwacold lori konga pe ko ṣiṣẹ, kọsitọmá kẹbọt kò rán mi lọ́wọ́.
```
Correction layer output:
```text
kiwacold lori KongaPay ko sise kositoma kebot ko ran mi lowo
```
Corrections applied:
- `konga pe` -> `KongaPay` (provider)
Remaining missing entities: QR Code, customer care

## S043 - identity_security

Audio: ``
Expected entities: BVN, NIN, KYC, OTP
Raw score: 0.5000
Corrected score: 0.7500

Raw N-ATLaS transcript:
```text
mo fẹ́ sọ bvn àti ni imọ-account mi fún kys, ṣùgbọ́n otp kò dé
```
Correction layer output:
```text
mo fe so BVN ati ni imo account mi fun KYC sugbon OTP ko de
```
Corrections applied:
- `bvn` -> `BVN` (identity)
- `kys` -> `KYC` (identity)
- `otp` -> `OTP` (security_term)
Remaining missing entities: NIN

## S044 - security_terms

Audio: ``
Expected entities: OTP, PIN, password
Raw score: 0.6667
Corrected score: 0.6667

Raw N-ATLaS transcript:
```text
mo gbàgbé pín àti password mi, ṣùgbọ́n apu kò gba verification.
```
Correction layer output:
```text
mo gbagbe PIN ati password mi sugbon apu ko gba verification
```
Corrections applied:
- `password` -> `password` (security_term)
- `pin` -> `PIN` (security_term)
Remaining missing entities: OTP

## S045 - payment_infrastructure_terms

Audio: ``
Expected entities: NIBSS, Session ID, NIP, NUBAN
Raw score: 0.2500
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
bífíìsì nílò sẹ́sọ́nàìlì àti nípa dító fún núbà àkọ́ọ̀tì nọ́mbà
```
Correction layer output:
```text
NIBSS nilo Session ID ati NIP dito fun NUBAN Nomba
```
Corrections applied:
- `nuba akooti` -> `NUBAN` (transaction_term)
- `sesonaili` -> `Session ID` (transaction_term)
- `bifiisi` -> `NIBSS` (payment_infrastructure)
- `nomba` -> `Nomba` (provider)
- `nibss` -> `NIBSS` (payment_infrastructure)
- `nuban` -> `NUBAN` (transaction_term)
- `nipa` -> `NIP` (transaction_term)
- `nip` -> `NIP` (transaction_term)
Remaining missing entities: none

## S046 - fraud_legal_transfer_issue

Audio: ``
Expected entities: unauthorized debit, scam, wrong recipient, court order
Raw score: 0.2500
Corrected score: 0.7500

Raw N-ATLaS transcript:
```text
mo rí onàfíríísì débìt, wọn ní oúnjẹ scam, ṣùgbọ́n ráńgùn rẹ̀ sípíẹ̀ńtì náà ló kọ́tọ́ọ̀dà.
```
Correction layer output:
```text
mo ri unauthorized debit won ni ounje scam sugbon rangun re sipienti naa lo court order
```
Corrections applied:
- `onafiriisi debit` -> `unauthorized debit` (fraud_term)
- `kotooda` -> `court order` (legal_term)
- `debit` -> `debit` (payment_term)
- `scam` -> `scam` (fraud_term)
Remaining missing entities: wrong recipient

## S047 - beneficiary_card_terms

Audio: ``
Expected entities: beneficiary, credit, debit card, virtual card
Raw score: 0.7500
Corrected score: 0.7500

Raw N-ATLaS transcript:
```text
bẹẹfiṣiari kò rí credit, debit card àti virtual card méjèèjì ní iṣu
```
Correction layer output:
```text
beefisiari ko ri credit debit card ati virtual card mejeeji ni isu
```
Corrections applied:
- `virtual card` -> `virtual card` (payment_term)
- `debit card` -> `debit card` (payment_term)
- `credit` -> `credit` (payment_term)
- `debit` -> `debit` (payment_term)
Remaining missing entities: beneficiary

## S048 - critical_variant_opay

Audio: ``
Expected entities: OPay, failed transfer, GTBank
Raw score: 0.0000
Corrected score: 0.6667

Raw N-ATLaS transcript:
```text
òpè transfer mi kùnà sí gt bank.
```
Correction layer output:
```text
OPay mi kuna si GTBank
```
Corrections applied:
- `ope transfer` -> `OPay` (provider)
- `gt bank` -> `GTBank` (bank)
- `gtbank` -> `GTBank` (bank)
- `opay` -> `OPay` (provider)
Remaining missing entities: failed transfer

## S049 - critical_variant_opay

Audio: ``
Expected entities: OPay, Session ID
Raw score: 0.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
kò pé mi kò fi sẹ́sọ́náídì ń
```
Correction layer output:
```text
OPay mi ko fi Session ID n
```
Corrections applied:
- `sesonaidi` -> `Session ID` (transaction_term)
- `ko pe` -> `OPay` (provider)
- `opay` -> `OPay` (provider)
Remaining missing entities: none

## S050 - critical_variant_opay

Audio: ``
Expected entities: OPay, POS, double debit
Raw score: 0.0000
Corrected score: 0.6667

Raw N-ATLaS transcript:
```text
òpè píẹ̀sí jẹntina mi dọ́bùdẹ́bìtì
```
Correction layer output:
```text
OPay piesi jentina mi double debit
```
Corrections applied:
- `dobudebiti` -> `double debit` (payment_term)
- `debit` -> `debit` (payment_term)
- `ope` -> `OPay` (provider)
Remaining missing entities: POS

## S051 - critical_variant_opay

Audio: ``
Expected entities: OPay, reversal, receipt
Raw score: 0.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
mo fẹ́ rẹ́và sál lórí òpè irìsí ti mi
```
Correction layer output:
```text
mo fe reversal lori OPay receipt mi
```
Corrections applied:
- `irisi ti` -> `receipt` (transaction_term)
- `reva sal` -> `reversal` (support_term)
- `receipt` -> `receipt` (transaction_term)
- `ope` -> `OPay` (provider)
Remaining missing entities: none

## S052 - critical_variant_palmpay

Audio: ``
Expected entities: PalmPay, Access Bank, pending
Raw score: 0.6667
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
pampe si access bank wa ni pending
```
Correction layer output:
```text
PalmPay Access Bank Bank wa ni pending
```
Corrections applied:
- `access bank` -> `Access Bank` (bank)
- `pampe si` -> `PalmPay` (provider)
- `palmpay` -> `PalmPay` (provider)
- `pending` -> `pending` (status)
- `access` -> `Access Bank` (bank)
Remaining missing entities: none

## S053 - critical_variant_palmpay

Audio: ``
Expected entities: PalmPay, receipt, transaction reference
Raw score: 0.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
paunpé rí síìtì mi ni transactions rẹ́fùrànísì tí kò pé.
```
Correction layer output:
```text
PalmPay receipt mi ni transactions transaction reference ti OPay
```
Corrections applied:
- `refuranisi` -> `transaction reference` (transaction_term)
- `ri siiti` -> `receipt` (transaction_term)
- `receipt` -> `receipt` (transaction_term)
- `paunpe` -> `PalmPay` (provider)
- `ko pe` -> `OPay` (provider)
- `opay` -> `OPay` (provider)
Remaining missing entities: none

## S054 - critical_variant_palmpay

Audio: ``
Expected entities: PalmPay, BVN, KYC
Raw score: 0.3333
Corrected score: 0.6667

Raw N-ATLaS transcript:
```text
mo fẹ́ líńbí-vnm lórí páńpè fún kyc
```
Correction layer output:
```text
mo fe linbi vnm lori PalmPay fun KYC
```
Corrections applied:
- `panpe` -> `PalmPay` (provider)
- `kyc` -> `KYC` (identity)
Remaining missing entities: BVN

## S055 - critical_variant_palmpay

Audio: ``
Expected entities: PalmPay, customer care, bot
Raw score: 0.3333
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
pámpé kọ́stọ́má kíẹ̀ bọ́t kò dáhùn.
```
Correction layer output:
```text
PalmPay customer care kie bot ko dahun
```
Corrections applied:
- `kostoma` -> `customer care` (support_term)
- `pampe` -> `PalmPay` (provider)
- `bot` -> `bot` (support_term)
Remaining missing entities: none

## S056 - critical_variant_moniepoint

Audio: ``
Expected entities: Moniepoint, POS, timeout, NIP
Raw score: 0.0000
Corrected score: 0.5000

Raw N-ATLaS transcript:
```text
mọ́ní pọ́ǹt p.o.s.míní tíimọ̀tù lórí níbi tíránfà.
```
Correction layer output:
```text
Moniepoint POS mini tiimotu lori nibi failed transfer
```
Corrections applied:
- `moni pont` -> `Moniepoint` (provider)
- `tiranfa` -> `failed transfer` (support_term)
- `p o s` -> `POS` (channel)
- `pos` -> `POS` (channel)
Remaining missing entities: timeout, NIP

## S057 - critical_variant_moniepoint

Audio: ``
Expected entities: Moniepoint, successful
Raw score: 0.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
mo ní pọ́ń ẹjàn sọ pé ṣanṣẹ́sọ̀sífọ̀
```
Correction layer output:
```text
mo ni Moniepoint so pe successful
```
Corrections applied:
- `sansesosifo` -> `successful` (status)
- `successful` -> `successful` (status)
- `pon ejan` -> `Moniepoint` (provider)
Remaining missing entities: none

## S058 - critical_variant_moniepoint

Audio: ``
Expected entities: Moniepoint, dispute, double debit
Raw score: 0.3333
Corrected score: 0.6667

Raw N-ATLaS transcript:
```text
mo fẹ́ dispute fun money-poin dọ́bú dẹ́bít.
```
Correction layer output:
```text
mo fe dispute fun Moniepoint dobu debit
```
Corrections applied:
- `money poin` -> `Moniepoint` (provider)
- `dispute` -> `dispute` (support_term)
- `debit` -> `debit` (payment_term)
Remaining missing entities: double debit

## S059 - critical_variant_kuda

Audio: ``
Expected entities: Kuda, Zenith Bank, pending
Raw score: 0.6667
Corrected score: 0.6667

Raw N-ATLaS transcript:
```text
colder c zenith bank transfer wa ni pending
```
Correction layer output:
```text
colder c Zenith Bank Bank transfer wa ni pending
```
Corrections applied:
- `zenith bank` -> `Zenith Bank` (bank)
- `pending` -> `pending` (status)
- `zenith` -> `Zenith Bank` (bank)
Remaining missing entities: Kuda

## S060 - critical_variant_kuda

Audio: ``
Expected entities: Kuda, NIN, BVN
Raw score: 0.6667
Corrected score: 0.6667

Raw N-ATLaS transcript:
```text
kúdà bẹ́rẹ̀ fún ní àti bvn.
```
Correction layer output:
```text
Kuda bere fun ni ati BVN
```
Corrections applied:
- `kuda` -> `Kuda` (provider)
- `kuda` -> `Kuda` (provider)
- `bvn` -> `BVN` (identity)
Remaining missing entities: NIN

## S061 - critical_variant_kuda

Audio: ``
Expected entities: Kuda, debit card, ATM
Raw score: 0.6667
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
kọ́dà debit card kò ṣiṣẹ́ lórí atm
```
Correction layer output:
```text
Kuda debit card ko sise lori ATM
```
Corrections applied:
- `debit card` -> `debit card` (payment_term)
- `debit` -> `debit` (payment_term)
- `koda` -> `Kuda` (provider)
- `atm` -> `ATM` (channel)
Remaining missing entities: none

## S062 - critical_variant_paga

Audio: ``
Expected entities: Paga, USSD, wallet balance
Raw score: 0.3333
Corrected score: 0.6667

Raw N-ATLaS transcript:
```text
pàga usd-cold kò fi wálẹ̀t balanṣán.
```
Correction layer output:
```text
Paga USSD cold ko fi walet balansan
```
Corrections applied:
- `paga` -> `Paga` (provider)
- `usd` -> `USSD` (channel)
Remaining missing entities: wallet balance

## S063 - critical_variant_paga

Audio: ``
Expected entities: Paga, account restricted, KYC
Raw score: 0.6667
Corrected score: 0.6667

Raw N-ATLaS transcript:
```text
pàga àkáùntì restricted nítorí kyc
```
Correction layer output:
```text
Paga akaunti restricted nitori KYC
```
Corrections applied:
- `paga` -> `Paga` (provider)
- `kyc` -> `KYC` (identity)
Remaining missing entities: account restricted

## S064 - critical_variant_paga

Audio: ``
Expected entities: Paga, Session ID
Raw score: 0.5000
Corrected score: 0.5000

Raw N-ATLaS transcript:
```text
pàgá transfer nílò ṣẹ́ṣẹ́ náìdì.
```
Correction layer output:
```text
Paga transfer nilo sese naidi
```
Corrections applied:
- `paga` -> `Paga` (provider)
Remaining missing entities: Session ID

## S065 - critical_variant_access_bank

Audio: ``
Expected entities: Access Bank, credit, OPay
Raw score: 0.3333
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
acess banko rí credit láti o pe
```
Correction layer output:
```text
Access Bank Bank ri credit lati OPay
```
Corrections applied:
- `acess banko` -> `Access Bank` (bank)
- `access` -> `Access Bank` (bank)
- `credit` -> `credit` (payment_term)
- `o pe` -> `OPay` (provider)
Remaining missing entities: none

## S066 - critical_variant_access_bank

Audio: ``
Expected entities: Access Bank, beneficiary
Raw score: 0.5000
Corrected score: 0.5000

Raw N-ATLaS transcript:
```text
access bank benifitary ní èmi yàtò
```
Correction layer output:
```text
Access Bank Bank benifitary ni emi yato
```
Corrections applied:
- `access bank` -> `Access Bank` (bank)
- `access` -> `Access Bank` (bank)
Remaining missing entities: beneficiary

## S067 - critical_variant_access_bank

Audio: ``
Expected entities: Access Bank, transaction reference
Raw score: 0.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
assess bank transaction rẹfẹrẹns kohán
```
Correction layer output:
```text
Access Bank Bank transaction reference kohan
```
Corrections applied:
- `transaction referens` -> `transaction reference` (transaction_term)
- `assess bank` -> `Access Bank` (bank)
- `access` -> `Access Bank` (bank)
Remaining missing entities: none

## S068 - critical_variant_gtbank

Audio: ``
Expected entities: GTBank, PalmPay, failed transfer
Raw score: 0.0000
Corrected score: 0.6667

Raw N-ATLaS transcript:
```text
gti ban transfer lati pampe efeld
```
Correction layer output:
```text
GTBank transfer lati PalmPay efeld
```
Corrections applied:
- `gti ban` -> `GTBank` (bank)
- `gtbank` -> `GTBank` (bank)
- `pampe` -> `PalmPay` (provider)
Remaining missing entities: failed transfer

## S069 - critical_variant_gtbank

Audio: ``
Expected entities: GTBank, receipt, Session ID
Raw score: 0.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
gítí bank rìsíìtì nílò ṣẹ̀ṣàn id.
```
Correction layer output:
```text
GTBank receipt nilo Session ID
```
Corrections applied:
- `giti bank` -> `GTBank` (bank)
- `sesan id` -> `Session ID` (transaction_term)
- `risiiti` -> `receipt` (transaction_term)
- `gtbank` -> `GTBank` (bank)
Remaining missing entities: none

## S070 - critical_variant_gtbank

Audio: ``
Expected entities: GTBank, POS, chargeback
Raw score: 0.3333
Corrected score: 0.6667

Raw N-ATLaS transcript:
```text
jíti bank card ló ri peos ni chargeback
```
Correction layer output:
```text
GTBank card lo ri peos ni chargeback
```
Corrections applied:
- `chargeback` -> `chargeback` (support_term)
- `jiti bank` -> `GTBank` (bank)
- `gtbank` -> `GTBank` (bank)
Remaining missing entities: POS

## S071 - critical_variant_zenith_bank

Audio: ``
Expected entities: Zenith Bank, wallet balance
Raw score: 0.5000
Corrected score: 0.5000

Raw N-ATLaS transcript:
```text
zenith bank alaad de sugbon balaadns ko yipada
```
Correction layer output:
```text
Zenith Bank Bank de sugbon balaadns ko yipada
```
Corrections applied:
- `zenith bank alaad` -> `Zenith Bank` (bank)
- `zenith bank` -> `Zenith Bank` (bank)
- `zenith` -> `Zenith Bank` (bank)
Remaining missing entities: wallet balance

## S072 - critical_variant_zenith_bank

Audio: ``
Expected entities: Zenith Bank, NIP, timeout
Raw score: 0.6667
Corrected score: 0.6667

Raw N-ATLaS transcript:
```text
zenith bánk nip ọ̀pọ̀ ní thymealt.
```
Correction layer output:
```text
Zenith Bank Bank NIP opo ni thymealt
```
Corrections applied:
- `zenith bank` -> `Zenith Bank` (bank)
- `zenith` -> `Zenith Bank` (bank)
- `nip` -> `NIP` (transaction_term)
Remaining missing entities: timeout

## S073 - critical_variant_zenith_bank

Audio: ``
Expected entities: Zenith Bank, wrong recipient, court order
Raw score: 0.3333
Corrected score: 0.6667

Raw N-ATLaS transcript:
```text
Senate bank rong recipient nilo court order.
```
Correction layer output:
```text
Zenith Bank Bank wrong beneficiary nilo court order
```
Corrections applied:
- `rong recipient` -> `wrong recipient` (transfer_issue)
- `senate bank` -> `Zenith Bank` (bank)
- `court order` -> `court order` (legal_term)
- `recipient` -> `beneficiary` (transfer_term)
- `zenith` -> `Zenith Bank` (bank)
Remaining missing entities: wrong recipient

## S074 - critical_variant_bvn

Audio: ``
Expected entities: BVN, NIN, KYC
Raw score: 0.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
bífí ẹ̀mí kò máátì ní mi lórí kíwáísí
```
Correction layer output:
```text
BVN ko maati NIN lori KYC
```
Corrections applied:
- `bifi emi` -> `BVN` (identity)
- `kiwaisi` -> `KYC` (identity)
- `ni mi` -> `NIN` (identity)
- `bvn` -> `BVN` (identity)
- `nin` -> `NIN` (identity)
- `kyc` -> `KYC` (identity)
Remaining missing entities: none

## S075 - critical_variant_bvn

Audio: ``
Expected entities: BVN, PalmPay
Raw score: 0.0000
Corrected score: 0.5000

Raw N-ATLaS transcript:
```text
mo fẹ́ kọ́rẹ́ gbé vẹ̀n lórí pampe
```
Correction layer output:
```text
mo fe kore gbe ven lori PalmPay
```
Corrections applied:
- `pampe` -> `PalmPay` (provider)
Remaining missing entities: BVN

## S076 - critical_variant_bvn

Audio: ``
Expected entities: BVN, OTP
Raw score: 0.5000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
bíbi ẹ́nbẹ̀ fikasion kò gba otp.
```
Correction layer output:
```text
BVN enbe fikasion ko gba OTP
```
Corrections applied:
- `bibi` -> `BVN` (identity)
- `bvn` -> `BVN` (identity)
- `otp` -> `OTP` (security_term)
Remaining missing entities: none

## S077 - critical_variant_session_id

Audio: ``
Expected entities: Session ID, receipt
Raw score: 0.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
níbo ni ṣẹ̀ṣàn-àdí wà lórí rí síìtì?
```
Correction layer output:
```text
nibo ni Session ID wa lori receipt
```
Corrections applied:
- `sesan adi` -> `Session ID` (transaction_term)
- `ri siiti` -> `receipt` (transaction_term)
- `receipt` -> `receipt` (transaction_term)
Remaining missing entities: none

## S078 - critical_variant_session_id

Audio: ``
Expected entities: NIBSS, Session ID
Raw score: 0.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
dbs sestrize bẹrẹ fun sessional id
```
Correction layer output:
```text
NIBSS sestrize bere fun Session ID
```
Corrections applied:
- `sessional id` -> `Session ID` (transaction_term)
- `session id` -> `Session ID` (transaction_term)
- `dbs` -> `NIBSS` (payment_infrastructure)
Remaining missing entities: none

## S079 - critical_variant_session_id

Audio: ``
Expected entities: Session ID, OPay
Raw score: 0.0000
Corrected score: 0.5000

Raw N-ATLaS transcript:
```text
sẹ́ṣùn áìdí lórí ò pé táǹṣfà kọ́ han
```
Correction layer output:
```text
sesun aidi lori OPay tansfa ko han
```
Corrections applied:
- `o pe` -> `OPay` (provider)
Remaining missing entities: Session ID

## S080 - critical_variant_session_id

Audio: ``
Expected entities: beneficiary, Session ID
Raw score: 0.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
bánkì bẹ̀nífíṣẹ́ rì nílò sẹ́sọ́ń-ń-ń-dì
```
Correction layer output:
```text
banki beneficiary nilo Session ID
```
Corrections applied:
- `seson n n di` -> `Session ID` (transaction_term)
- `benifise ri` -> `beneficiary` (transfer_term)
- `session id` -> `Session ID` (transaction_term)
Remaining missing entities: none

## S081 - critical_variant_transaction_reference

Audio: ``
Expected entities: transaction reference, transaction history
Raw score: 0.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
tranfrẹnse mi kó nínú tranfrẹnse ìstrè
```
Correction layer output:
```text
transaction reference mi ko ninu transaction reference transaction history
```
Corrections applied:
- `tranfrense` -> `transaction reference` (transaction_term)
- `istre` -> `transaction history` (support_term)
Remaining missing entities: none

## S082 - critical_variant_transaction_reference

Audio: ``
Expected entities: transaction reference, receipt
Raw score: 1.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
mo ní transaction reference sùgbọ́n kò sí receipt.
```
Correction layer output:
```text
mo ni transaction reference sugbon ko si receipt
```
Corrections applied:
- `transaction reference` -> `transaction reference` (transaction_term)
- `receipt` -> `receipt` (transaction_term)
Remaining missing entities: none

## S083 - critical_variant_transaction_reference

Audio: ``
Expected entities: customer care, transaction reference
Raw score: 1.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
customer care béré fún transaction reference.
```
Correction layer output:
```text
customer care bere fun transaction reference
```
Corrections applied:
- `transaction reference` -> `transaction reference` (transaction_term)
- `customer care` -> `customer care` (support_term)
Remaining missing entities: none

## S084 - critical_variant_debit

Audio: ``
Expected entities: debit
Raw score: 0.0000
Corrected score: 1.0000

Raw N-ATLaS transcript:
```text
mo rí débì tí mì ò mọ
```
Correction layer output:
```text
mo ri debit ti mi o mo
```
Corrections applied:
- `debi` -> `debit` (payment_term)
Remaining missing entities: none

## S085 - critical_variant_debit

Audio: ``
Expected entities: double debit, POS
Raw score: 0.0000
Corrected score: 0.5000

Raw N-ATLaS transcript:
```text
dọ́bùdẹ̀ bí i ṣẹlẹ̀ lórí p.o.s.
```
Correction layer output:
```text
dobude bi i sele lori POS
```
Corrections applied:
- `p o s` -> `POS` (channel)
- `pos` -> `POS` (channel)
Remaining missing entities: double debit

## S086 - critical_variant_debit

Audio: ``
Expected entities: unauthorized debit, virtual card
Raw score: 0.5000
Corrected score: 0.5000

Raw N-ATLaS transcript:
```text
unterized débits wa lori virtual card
```
Correction layer output:
```text
unterized debit wa lori virtual card
```
Corrections applied:
- `virtual card` -> `virtual card` (payment_term)
- `debits` -> `debit` (payment_term)
- `debit` -> `debit` (payment_term)
Remaining missing entities: unauthorized debit
