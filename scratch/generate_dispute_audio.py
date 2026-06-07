import os
import json
import zipfile
from dotenv import load_dotenv
from spitch import Spitch

# Load environment variables
load_dotenv()
api_key = os.getenv("SPITCH_API_KEY")

if not api_key:
    raise ValueError("SPITCH_API_KEY not found in environment variables. Please check your .env file.")

client = Spitch(api_key=api_key)

# Define the 20 Yoruba financial support queries
queries = [
    {
        "id": "Q01",
        "text": "Ẹ jọọ gbigbe owo mi kuna lori OPay owo mi si ti senu",
        "translation": "Please my transfer failed on OPay and my money has been debited.",
        "voice": "femi",
        "category": "failed_transfer_opay"
    },
    {
        "id": "Q02",
        "text": "Mo gbe owo lati PalmPay si Access Bank sugbon o kuna owo mi si ti lo",
        "translation": "I transferred money from PalmPay to Access Bank but it failed and my money was debited.",
        "voice": "sade",
        "category": "failed_transfer_palmpay"
    },
    {
        "id": "Q03",
        "text": "Owo mi ti sọnu lori Moniepoint lẹhin gbigbe owo to kuna",
        "translation": "My money is lost on Moniepoint after a failed transfer.",
        "voice": "segun",
        "category": "failed_transfer_moniepoint"
    },
    {
        "id": "Q04",
        "text": "PalmPay mi ti dina nitori KYC mi o le gbe owo jade",
        "translation": "My PalmPay is restricted because of KYC, I cannot withdraw money.",
        "voice": "funmi",
        "category": "account_restricted_kyc"
    },
    {
        "id": "Q05",
        "text": "Mo ṣi owo firanṣẹ si akọọlẹ miiran lori OPay",
        "translation": "I mistakenly sent money to another account on OPay.",
        "voice": "femi",
        "category": "erroneous_transfer"
    },
    {
        "id": "Q06",
        "text": "Nibo ni mo ti le ri Session ID fun gbigbe owo to kuna?",
        "translation": "Where can I find the Session ID for my failed transfer?",
        "voice": "sade",
        "category": "session_id_query"
    },
    {
        "id": "Q07",
        "text": "Bawo ni mo ṣe le so BVN ati NIN mi pọ mọ OPay lati gbe owo soke?",
        "translation": "How do I link my BVN and NIN to OPay to increase my limit?",
        "voice": "segun",
        "category": "kyc_upgrade"
    },
    {
        "id": "Q08",
        "text": "Account mi ti dina nitori won ri iwa ifura lori re",
        "translation": "My account has been blocked because they saw suspicious activity on it.",
        "voice": "funmi",
        "category": "security_freeze"
    },
    {
        "id": "Q09",
        "text": "Won na mi ni owo lẹmeji fun rira eyo kan",
        "translation": "I was debited twice for a single purchase.",
        "voice": "femi",
        "category": "double_debit"
    },
    {
        "id": "Q10",
        "text": "O ti to wakati meji-le-logoji ti mo ti n duro de reversal mi",
        "translation": "It has been 48 hours that I have been waiting for my reversal.",
        "voice": "sade",
        "category": "delayed_reversal"
    },
    {
        "id": "Q11",
        "text": "Mo fe ri transaction history mi lati osu to koja",
        "translation": "I want to see my transaction history from last month.",
        "voice": "segun",
        "category": "transaction_history"
    },
    {
        "id": "Q12",
        "text": "App OPay mi n crash nigba ti mo ba fe gbe owo",
        "translation": "My OPay app crashes when I want to transfer money.",
        "voice": "funmi",
        "category": "app_issue"
    },
    {
        "id": "Q13",
        "text": "Debit card mi o sise lori ATM mo fe mo idi ti o fi ri bee",
        "translation": "My debit card is not working on the ATM, I want to know why.",
        "voice": "femi",
        "category": "card_issue"
    },
    {
        "id": "Q14",
        "text": "Mo ri debit ti mi o mo nipa re lori account mi",
        "translation": "I saw a debit that I do not know about on my account.",
        "voice": "sade",
        "category": "unrecognized_debit"
    },
    {
        "id": "Q15",
        "text": "Won ni mo ti de daily transfer limit mi sugbon mo nilo lati gbe owo pajawiri",
        "translation": "They said I reached my daily transfer limit but I need to make an emergency transfer.",
        "voice": "segun",
        "category": "limit_reached"
    },
    {
        "id": "Q16",
        "text": "Bawo ni mo se le se atunse si BVN mi ti o wa lori PalmPay?",
        "translation": "How can I correct my BVN that is on PalmPay?",
        "voice": "funmi",
        "category": "bvn_correction"
    },
    {
        "id": "Q17",
        "text": "Koodu USSD wo ni mo le lo lati wo balance mi lori OPay?",
        "translation": "What USSD code can I use to check my balance on OPay?",
        "voice": "femi",
        "category": "ussd_balance"
    },
    {
        "id": "Q18",
        "text": "Oruko ti o han nigba ti mo fe gbe owo yato si oruko to ye ko han",
        "translation": "The name that appeared when I wanted to transfer money is different from the name that should appear.",
        "voice": "sade",
        "category": "wrong_recipient_name"
    },
    {
        "id": "Q19",
        "text": "E joo e ran mi lowo won ti se scam mi lori OPay won gbe gbogbo owo mi lo",
        "translation": "Please help me, I have been scammed on OPay, they took all my money.",
        "voice": "segun",
        "category": "scam_complaint"
    },
    {
        "id": "Q20",
        "text": "Bawo ni mo se le ba customer care gidi soro yato si bot yii?",
        "translation": "How can I speak to a real customer care agent instead of this bot?",
        "voice": "funmi",
        "category": "agent_escalation"
    }
]

# Set up paths
scratch_dir = os.path.dirname(__file__)
audio_dir = os.path.join(scratch_dir, "dispute_audio")
os.makedirs(audio_dir, exist_ok=True)

metadata_list = []

print("Starting generation of Yoruba synthetic financial dispute dataset...")
print(f"Destination: {audio_dir}")

for idx, q in enumerate(queries):
    filename = f"{q['id']}_{q['voice']}_{q['category']}.wav"
    filepath = os.path.join(audio_dir, filename)
    
    print(f"[{idx+1}/20] Generating audio for query {q['id']} ({q['voice']})...")
    
    try:
        response = client.speech.generate(
            language="yo",
            text=q["text"],
            voice=q["voice"]
        )
        audio_data = response.read()
        
        with open(filepath, "wb") as f:
            f.write(audio_data)
            
        q["audio_filename"] = filename
        metadata_list.append(q)
        
    except Exception as e:
        print(f"  FAILED: Error generating audio for {q['id']}: {e}")

# Save metadata json
metadata_path = os.path.join(scratch_dir, "dispute_metadata.json")
with open(metadata_path, "w", encoding="utf-8") as f:
    json.dump(metadata_list, f, indent=2, ensure_ascii=False)
print(f"Saved metadata file to {metadata_path}")

# Zip all generated audios and metadata
zip_path = os.path.join(scratch_dir, "yoruba_fintech_benchmark.zip")
print(f"Creating ZIP archive at {zip_path}...")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    # Add metadata
    zipf.write(metadata_path, "dispute_metadata.json")
    # Add audios
    for root, dirs, files in os.walk(audio_dir):
        for file in files:
            file_path = os.path.join(root, file)
            zipf.write(file_path, os.path.join("dispute_audio", file))

print("ZIP archive created successfully!")
print("Dataset generation complete!")
