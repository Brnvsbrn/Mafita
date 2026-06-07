import os
import json
from dotenv import load_dotenv
from spitch import Spitch

load_dotenv()
api_key = os.getenv("SPITCH_API_KEY")
client = Spitch(api_key=api_key)

# The 20 raw Yoruba financial support queries
queries = [
    {"id": "Q01", "text": "Ẹ jọọ gbigbe owo mi kuna lori OPay owo mi si ti senu"},
    {"id": "Q02", "text": "Mo gbe owo lati PalmPay si Access Bank sugbon o kuna owo mi si ti lo"},
    {"id": "Q03", "text": "Owo mi ti sọnu lori Moniepoint lẹhin gbigbe owo to kuna"},
    {"id": "Q04", "text": "PalmPay mi ti dina nitori KYC mi o le gbe owo jade"},
    {"id": "Q05", "text": "Mo ṣi owo firanṣẹ si akọọlẹ miiran lori OPay"},
    {"id": "Q06", "text": "Nibo ni mo ti le ri Session ID fun gbigbe owo to kuna?"},
    {"id": "Q07", "text": "Bawo ni mo ṣe le so BVN ati NIN mi pọ mọ OPay lati gbe owo soke?"},
    {"id": "Q08", "text": "Account mi ti dina nitori won ri iwa ifura lori re"},
    {"id": "Q09", "text": "Won na mi ni owo lẹmeji fun rira eyo kan"},
    {"id": "Q10", "text": "O ti to wakati meji-le-logoji ti mo ti n duro de reversal mi"},
    {"id": "Q11", "text": "Mo fe ri transaction history mi lati osu to koja"},
    {"id": "Q12", "text": "App OPay mi n crash nigba ti mo ba fe gbe owo"},
    {"id": "Q13", "text": "Debit card mi o sise lori ATM mo fe mo idi ti o fi ri bee"},
    {"id": "Q14", "text": "Mo ri debit ti mi o mo nipa re lori account mi"},
    {"id": "Q15", "text": "Won ni mo ti de daily transfer limit mi sugbon mo nilo lati gbe owo pajawiri"},
    {"id": "Q16", "text": "Bawo ni mo se le se atunse si BVN mi ti o wa lori PalmPay?"},
    {"id": "Q17", "text": "Koodu USSD wo ni mo le lo lati wo balance mi lori OPay?"},
    {"id": "Q18", "text": "Oruko ti o han nigba ti mo fe gbe owo yato si oruko to ye ko han"},
    {"id": "Q19", "text": "E joo e ran mi lowo won ti se scam mi lori OPay won gbe gbogbo owo mi lo"},
    {"id": "Q20", "text": "Bawo ni mo se le ba customer care gidi soro yato si bot yii?"}
]

print("Calling Spitch tone_mark API for all 20 queries...")
auto_results = []

for idx, q in enumerate(queries):
    print(f"[{idx+1}/20] Processing {q['id']}...")
    try:
        result = client.text.tone_mark(
            language="yo",
            text=q["text"]
        )
        q["auto_restored"] = result.text
    except Exception as e:
        print(f"  Failed for {q['id']}: {e}")
        q["auto_restored"] = q["text"]
    auto_results.append(q)

output_path = os.path.join(os.path.dirname(__file__), "auto_tone_marked_queries.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(auto_results, f, indent=2, ensure_ascii=False)

print(f"Saved auto diacritized results to {output_path}")
