import os
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FALLBACK_DIACRITICS = {
    "Bawo ni, kini mo le ran e lowo loni?": "Báwo ni, kí ni mo lè ràn ẹ́ lọ́wọ́ lónìí?",
    "Bawo ni, emi ni Mafita. Kini mo le ran e lowo loni?": "Báwo ni, èmi ni Mafita. Kí ni mo lè ràn ẹ́ lọ́wọ́ lónìí?",
    "Bawo ni, emi ni Mafita Agent. Kini mo le ran e lowo loni?": "Báwo ni, èmi ni Mafita Agent. Kí ni mo lè ràn ẹ́ lọ́wọ́ lónìí?",
    "Mo ri pe eyi je ikini.": "Mo rí pé èyí jẹ́ ìkíni.",
    "Ko si iwulo lati pe eto account fun eyi.": "Kò sí ìwúlò láti pe ètò account fún èyí.",
    "Mo ri pe o n beere ohun ti Mafita le se.": "Mo rí pé o ń béèrè ohun tí Mafita lè ṣe.",
    "Mo ri pe o n beere ohun ti Mafita Agent le se.": "Mo rí pé o ń béèrè ohun tí Mafita Agent lè ṣe.",
    "Mo pese akojopo ohun ti mo le ran e lowo lori Mafita.": "Mo pèsè àkójọpọ̀ ohun tí mo lè ràn ẹ́ lọ́wọ́ lórí Mafita.",
    "Mo le ran e lowo pelu pending transfer, failed transfer, double debit, KYC, Session ID, POS, card, ati wallet balance. So oro naa ni Yoruba tabi English, emi yoo si to o lailewu.": "Mo lè ràn ẹ́ lọ́wọ́ pẹ̀lú pending transfer, failed transfer, double debit, KYC, Session ID, POS, card, àti wallet balance. Sọ ọ̀rọ̀ náà ní Yorùbá tàbí English, èmi yóò sì tọ́ ọ láìléwu.",
    "Mo ri pe a nilo alaye olumulo ki eto le tesiwaju.": "Mo rí pé a nílò àlàyé olumulo kí ètò lè tẹ̀síwájú.",
    "Emi ko ni gboju le data account tabi transaction.": "Èmi kò ní gbójú lé data account tàbí transaction.",
    "Ki n le tesiwaju, jowo fi nomba foonu tabi oruko lori account Mafita re ranse, pelu transaction reference tabi Session ID.": "Kí n lè tẹ̀síwájú, jọ̀wọ́ fi nọ́mbà fóònù tàbí orúkọ lórí account Mafita rẹ ránṣẹ́, pẹ̀lú transaction reference tàbí Session ID.",
    "Ki n le tesiwaju, jowo fi transaction reference tabi Session ID fun oro yii ranse.": "Kí n lè tẹ̀síwájú, jọ̀wọ́ fi transaction reference tàbí Session ID fún ọ̀rọ̀ yìí ránṣẹ́.",
    "Ki n le tesiwaju, jowo fi nomba foonu tabi oruko lori account Mafita re ranse.": "Kí n lè tẹ̀síwájú, jọ̀wọ́ fi nọ́mbà fóònù tàbí orúkọ lórí account Mafita rẹ ránṣẹ́.",
    "Jowo so die sii ki n le ran o lowo.": "Jọ̀wọ́ sọ díẹ̀ sí i kí n lè ràn ọ́ lọ́wọ́.",
    "Mo ti sayewo record Mafita, mo si ti pese igbese to ye fun oro yii.": "Mo ti ṣàyẹ̀wò record Mafita, mo sì ti pèsè ìgbésẹ̀ tó yẹ fún ọ̀rọ̀ yìí.",
    "Oro yii nilo escalation. Mo ti pese re fun support/fraud team.": "Ọ̀rọ̀ yìí nílò escalation. Mo ti pèsè rẹ̀ fún support/fraud team.",
    "Jowo fi oruko/nomba foonu account ati transaction reference tabi Session ID ranse ki n le tesiwaju.": "Jọ̀wọ́ fi orúkọ/nọ́mbà fóònù account àti transaction reference tàbí Session ID ránṣẹ́ kí n lè tẹ̀síwájú.",
    "Jowo fi transaction reference tabi Session ID ranse ki n le topa oro yii.": "Jọ̀wọ́ fi transaction reference tàbí Session ID ránṣẹ́ kí n lè tọ́pa ọ̀rọ̀ yìí.",
    "Jowo fi nomba foonu account Mafita tabi oruko customer ranse.": "Jọ̀wọ́ fi nọ́mbà fóònù account Mafita tàbí orúkọ customer ránṣẹ́.",
    "Mo nilo alaye kan si ki n to le sise lori oro yii lailewu.": "Mo nílò àlàyé kan sí i kí n tó lè ṣiṣẹ́ lórí ọ̀rọ̀ yìí láìléwu.",
    "Jowo fi oruko/nomba foonu Mafita re ati transaction reference tabi Session ID ranse ki n le sayewo pending transfer ati reversal.": "Jọ̀wọ́ fi orúkọ/nọ́mbà fóònù Mafita rẹ àti transaction reference tàbí Session ID ránṣẹ́ kí n lè ṣàyẹ̀wò pending transfer àti reversal.",
    "Jowo fi oruko/nomba foonu Mafita re ati transaction reference, receipt, tabi Session ID ti o fe ki n topa ranse.": "Jọ̀wọ́ fi orúkọ/nọ́mbà fóònù Mafita rẹ àti transaction reference, receipt, tàbí Session ID tí o fẹ́ kí n tọ́pa ránṣẹ́.",
    "Jowo fi oruko/nomba foonu Mafita re, transaction reference tabi Session ID, iye owo ti a gba leemeji, merchant/POS terminal, ati akoko debit mejeeji ranse.": "Jọ̀wọ́ fi orúkọ/nọ́mbà fóònù Mafita rẹ, transaction reference tàbí Session ID, iye owó tí a gbà lẹ́ẹ̀mejì, merchant/POS terminal, àti àkókò debit méjèèjì ránṣẹ́.",
}


def _load_env():
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except Exception:
        pass


@lru_cache(maxsize=256)
def tone_mark_yoruba(text):
    clean = str(text or "").strip()
    if not clean:
        return clean
    if clean in FALLBACK_DIACRITICS:
        return FALLBACK_DIACRITICS[clean]

    _load_env()
    api_key = os.environ.get("SPITCH_API_KEY")
    if not api_key:
        return clean

    try:
        from spitch import Spitch

        result = Spitch(api_key=api_key).text.tone_mark(language="yo", text=clean)
        return getattr(result, "text", clean) or clean
    except Exception:
        return clean


def strip_diacritics(text):
    import unicodedata
    if not text:
        return ""
    nfd_form = unicodedata.normalize("NFD", str(text))
    return "".join(c for c in nfd_form if not unicodedata.combining(c))

