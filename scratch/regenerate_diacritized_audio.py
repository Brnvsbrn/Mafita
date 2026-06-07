import os
import json
import zipfile
from dotenv import load_dotenv
from spitch import Spitch

# Load environment variables
load_dotenv()
api_key = os.getenv("SPITCH_API_KEY")

if not api_key:
    raise ValueError("SPITCH_API_KEY not found in environment variables.")

client = Spitch(api_key=api_key)

# The meticulously cleaned, punctuated, and tone-corrected Yoruba financial support queries
queries = [
    {
        "id": "Q01",
        "text": "Ẹ jọ̀ọ́, gbígbé owó mi kùnà lórí OPay. Owó mi sì ti sọnù.",
        "translation": "Please my transfer failed on OPay and my money has been debited.",
        "voice": "femi",
        "category": "failed_transfer_opay"
    },
    {
        "id": "Q02",
        "text": "Mo gbé owó láti PalmPay sí Access Bank, ṣùgbọ́n ó kùnà. Owó mi sì ti lọ.",
        "translation": "I transferred money from PalmPay to Access Bank but it failed and my money was debited.",
        "voice": "sade",
        "category": "failed_transfer_palmpay"
    },
    {
        "id": "Q03",
        "text": "Owó mi ti sọnù lórí Moniepoint, lẹ́yìn gbígbé owó tó kùnà.",
        "translation": "My money is lost on Moniepoint after a failed transfer.",
        "voice": "segun",
        "category": "failed_transfer_moniepoint"
    },
    {
        "id": "Q04",
        "text": "PalmPay mi ti dínà nítorí KYC. Mi ò lè gbé owó jáde.",
        "translation": "My PalmPay is restricted because of KYC, I cannot withdraw money.",
        "voice": "funmi",
        "category": "account_restricted_kyc"
    },
    {
        "id": "Q05",
        "text": "Mo ṣì owó firánṣẹ́ sí akọó̀lẹ́ mìíràn lórí OPay.",
        "translation": "I mistakenly sent money to another account on OPay.",
        "voice": "femi",
        "category": "erroneous_transfer"
    },
    {
        "id": "Q06",
        "text": "Níbo ni mo ti lè rí Session ID, fún gbígbé owó tó kùnà?",
        "translation": "Where can I find the Session ID for my failed transfer?",
        "voice": "sade",
        "category": "session_id_query"
    },
    {
        "id": "Q07",
        "text": "Báwo ni mo ṣe lè sọ BVN àti NIN mi pọ̀ mọ́ OPay, láti gbé owó sókè?",
        "translation": "How do I link my BVN and NIN to OPay to increase my limit?",
        "voice": "segun",
        "category": "kyc_upgrade"
    },
    {
        "id": "Q08",
        "text": "Account mi ti dínà, nítorí wọ́n rí ìwà ìfura lórí rẹ̀.",
        "translation": "My account has been blocked because they saw suspicious activity on it.",
        "voice": "funmi",
        "category": "security_freeze"
    },
    {
        "id": "Q09",
        "text": "Wọ́n nà mí ní owó lẹ́mẹjì, fún ríra ẹyọ kan.",
        "translation": "I was debited twice for a single purchase.",
        "voice": "femi",
        "category": "double_debit"
    },
    {
        "id": "Q10",
        "text": "Ó ti tó wákàtí méjì-lé-lọ́gọ́jọ, tí mo ti ń dúró de reversal mi.",
        "translation": "It has been 48 hours that I have been waiting for my reversal.",
        "voice": "sade",
        "category": "delayed_reversal"
    },
    {
        "id": "Q11",
        "text": "Mo fẹ́ rí transaction history mi, láti oṣù tó kọjá.",
        "translation": "I want to see my transaction history from last month.",
        "voice": "segun",
        "category": "transaction_history"
    },
    {
        "id": "Q12",
        "text": "App OPay mi ń crash, nígbà tí mo bá fẹ́ gbé owó.",
        "translation": "My OPay app crashes when I want to transfer money.",
        "voice": "funmi",
        "category": "app_issue"
    },
    {
        "id": "Q13",
        "text": "Debit card mi ò ṣiṣẹ́ lórí ATM. Mo fẹ́ mọ ìdí tí ó fi rí bẹ́ẹ̀.",
        "translation": "My debit card is not working on the ATM, I want to know why.",
        "voice": "femi",
        "category": "card_issue"
    },
    {
        "id": "Q14",
        "text": "Mo rí debit tí mi ò mọ̀ nípa rẹ̀, lórí account mi.",
        "translation": "I saw a debit that I do not know about on my account.",
        "voice": "sade",
        "category": "unrecognized_debit"
    },
    {
        "id": "Q15",
        "text": "Wọ́n ní mo ti dé daily transfer limit mi, ṣùgbọ́n mo nílò láti gbé owó pàjáwìrì.",
        "translation": "They said I reached my daily transfer limit but I need to make an emergency transfer.",
        "voice": "segun",
        "category": "limit_reached"
    },
    {
        "id": "Q16",
        "text": "Báwo ni mo ṣe lè ṣe àtúnṣe, sí BVN mi tí ó wà lórí PalmPay?",
        "translation": "How can I correct my BVN that is on PalmPay?",
        "voice": "funmi",
        "category": "bvn_correction"
    },
    {
        "id": "Q17",
        "text": "Koodu USSD wo ni mo lè lo, láti wo balance mi lórí OPay?",
        "translation": "What USSD code can I use to check my balance on OPay?",
        "voice": "femi",
        "category": "ussd_balance"
    },
    {
        "id": "Q18",
        "text": "Orúkọ tí ó hàn nígbà tí mo fẹ́ gbé owó, yàtọ̀ sí orúkọ tó yẹ kó hàn.",
        "translation": "The name that appeared when I wanted to transfer money is different from the name that should appear.",
        "voice": "sade",
        "category": "wrong_recipient_name"
    },
    {
        "id": "Q19",
        "text": "Ẹ jọ̀ọ́, ẹ ràn mí lọ́wọ́! Wọn ti ṣe scam mi lórí OPay, wọ́n sì gbé gbogbo owó mi lọ.",
        "translation": "Please help me, I have been scammed on OPay, they took all my money.",
        "voice": "segun",
        "category": "scam_complaint"
    },
    {
        "id": "Q20",
        "text": "Báwo ni mo ṣe lè bá customer care gidi sọ̀rọ̀, yàtọ̀ sí bot yìí?",
        "translation": "How can I speak to a real customer care agent instead of this bot?",
        "voice": "funmi",
        "category": "agent_escalation"
    }
]

scratch_dir = os.path.dirname(__file__)
audio_dir = os.path.join(scratch_dir, "dispute_audio")
os.makedirs(audio_dir, exist_ok=True)

metadata_list = []

print("Starting RE-generation of Yoruba benchmark voice dataset with perfect diacritics and pacing...")

for idx, q in enumerate(queries):
    filename = f"{q['id']}_{q['voice']}_{q['category']}.wav"
    filepath = os.path.join(audio_dir, filename)
    
    print(f"[{idx+1}/20] Regenerating {q['id']} ({q['voice']})...")
    
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
        print(f"  FAILED for {q['id']}: {e}")

# Save updated metadata json
metadata_path = os.path.join(scratch_dir, "dispute_metadata.json")
with open(metadata_path, "w", encoding="utf-8") as f:
    json.dump(metadata_list, f, indent=2, ensure_ascii=False)
print(f"Saved updated metadata manifest to {metadata_path}")

# Zip all regenerated audios and metadata
zip_path = os.path.join(scratch_dir, "yoruba_fintech_benchmark.zip")
print(f"Updating ZIP archive at {zip_path}...")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    zipf.write(metadata_path, "dispute_metadata.json")
    for root, dirs, files in os.walk(audio_dir):
        for file in files:
            file_path = os.path.join(root, file)
            zipf.write(file_path, os.path.join("dispute_audio", file))

print("ZIP archive updated successfully with diacritics and natural pacing!")
print("Re-generation complete!")
