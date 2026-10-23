import asyncio
import logging
import os
import time
from datetime import datetime, timezone, timedelta
import feedparser
from telegram import Bot

# ==============================================================================
# CONFIGURATION & TELEGRAM SECRETS
# ==============================================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Maximum article age to process (15 minutes)
MAX_AGE_MINUTES = 15

# Indian Standard Timezone (UTC +5:30)
IST = timezone(timedelta(hours=5, minutes=30))

# ==============================================================================
# DEDICATED RSS SEARCH STREAMS
# ==============================================================================
RSS_FEEDS = [
    # 1. DGGI, Customs, Raids & Tax Evasion (Assam, Guwahati, Nagaland, Arunachal)
    "https://news.google.com/rss/search?q=DGGI+OR+tax+OR+raid+OR+seized+Assam+OR+Guwahati+OR+Nagaland&hl=en-IN&gl=IN&ceid=IN:en",
    
    # 2. Major Pan Masala & Gutkha Brands Nationwide
    "https://news.google.com/rss/search?q=Vimal+OR+Rajnigandha+OR+Pan+Parag+OR+Kamala+Pasand+OR+Shikhar+gutkha&hl=en-IN&gl=IN&ceid=IN:en",
    
    # 3. Burmese Supari & Betel Nut Smuggling (Northeast Transit Corridors)
    "https://news.google.com/rss/search?q=supari+OR+areca+nut+seized+Assam+OR+Mizoram+OR+Nagaland&hl=en-IN&gl=IN&ceid=IN:en",
    
    # 4. GST Council, Cess & Tobacco Policy/Tax Changes
    "https://news.google.com/rss/search?q=GST+Council+tax+hike+tobacco+OR+pan+masala+cess&hl=en-IN&gl=IN&ceid=IN:en",
    
    # 5. Cigarette & Tobacco Retail Price Revisions / MRP Increases
    "https://news.google.com/rss/search?q=cigarette+OR+pan+masala+price+hike+OR+RSP+increase+ITC&hl=en-IN&gl=IN&ceid=IN:en",
    
    # 6. Logistics, Freight Rates & Diesel Hikes
    "https://news.google.com/rss/search?q=diesel+price+hike+OR+freight+rate+increase+India+Assam&hl=en-IN&gl=IN&ceid=IN:en",
    
    # 7. Transporter Strikes & Highway Disruptions
    "https://news.google.com/rss/search?q=truckers+strike+OR+transport+cost+hike+cargo+tobacco&hl=en-IN&gl=IN&ceid=IN:en",

    # 8. Hawala, PMLA, Shell Companies & Regional Distributor Raids
    "https://news.google.com/rss/search?q=pan+masala+OR+gutkha+hawala+OR+money+laundering+OR+PMLA+Assam&hl=en-IN&gl=IN&ceid=IN:en"
]

# ==============================================================================
# COMPREHENSIVE 600+ KEYWORD DATABASE
# ==============================================================================
ALL_MONITORED_KEYWORDS = set([
    # 1. PAN MASALA & GUTKHA BRANDS
    "vimal", "vimal pan masala", "vimal kesar", "rajnigandha", "pan parag", 
    "rmd", "manikchand", "kamala pasand", "kamla pasand", "shikhar", "shikhar pan masala",
    "rajshree", "pan bahar", "pan vilas", "goa gutkha", "dilbagh", "tulsi", 
    "baba", "baba 120", "baba 160", "baba elaichi", "pass pass", "chaini khaini", 
    "miraj", "shahi spm", "mubarak", "sir", "aashiqui", "aashiqui gutkha", 
    "tansen", "rounak", "dinesh pouches", "red rose", "jmj", "jmj group", 
    "gagan", "gagan pan masala", "kuber", "kuber gutkha", "golden 17", 
    "ratna 300", "meetha mazaa", "gulab", "dilruba", "shahi gulab", "hans", 
    "hans chhap", "vimal bola", "shikhar premium", "cool lip", "gold mohar", 
    "swagat", "karamchand", "siggnature" , "action zarda" , "xgold" , "tara" , "dildaar" ,

    # 2. TOBACCO, ZARDA, KHAINI & SMOKELESS PRODUCTS
    "baba zarda", "tulsi zarda", "120 zarda", "160 zarda", "zafrani zarda", 
    "ratna zarda", "gopal zarda", "gopal 60", "gopal 132", "gopal 84", 
    "mircaj tobacco", "khaini", "raja khaini", "vimal khaini", "kuber khaini", 
    "chap khaini", "sarkar khaini", "swagat gold", "gutkha", "gutka", 
    "shikhar gutkha", "manikchand gutkha", "goa gutka", "m gutkha", "pan parag gutkha", 
    "zarda", "snus", "nicotine pouches", "chewing tobacco", "smokeless tobacco", 
    "slotted tobacco", "raw tobacco", "unmanufactured tobacco", "cut tobacco", 
    "tobacco paste", "mawa", "kharra", "dohra", "gul", "badshahi zarda", 
    "taaj zarda", "shahi zarda", "chhap tobacco", "black tobacco", "flavored tobacco",
    "scented zarda", "tobacco compound", "zarda compound", "gutkha compound",

    # 3. CIGARETTES, BIDIS & SMOKING PRODUCTS
    "itc", "gold flake", "classic", "wills", "navy cut", "capstan", 
    "scissors", "bristol", "flake", "godfrey phillips", "four square", "red & white", 
    "cavanders", "marlboro", "st moritz", "vazir sultan", "vst industries", "charminar", 
    "charms", "totem", "win", "paris", "djarum black", "essenza", 
    "indie mint", "gold flake kings", "classic milds", "classic menthol", "bidi", 
    "beedi", "501 bidi", "mangalore bidi", "30 bidi", "kailash bidi", "telephone bidi", 
    "ganesh bidi", "taj mahal bidi", "monkey bidi", "deshi bidi", "illegal cigarettes", 
    "smuggled cigarettes", "foreign cigarettes", "contraband cigarettes", "non duty paid", 
    "excise evade cigarettes", "loose cigarettes", "filter bidi", "unfiltered bidi", "cigars",

    # 4. PAAN, ARECA NUT, BETEL NUT & RAW MATERIALS
    "areca nut", "betel nut", "supari", "burmese supari", "myanmar supari", 
    "lanka supari", "indonesian supari", "raw supari", "dry supari", "cut supari", 
    "sweet supari", "scented supari", "chalia", "katha", "catechu", 
    "gambier", "slaked lime", "chuna", "menthol", "peppermint", 
    "spearmint", "essential oils", "saffron", "zafran", "kewda", 
    "kewra", "rose oil", "ruh gulab", "musk", "patchouli", 
    "sandalwood oil", "flavoring agents", "aromatic chemical", "betel leaf", "paan leaf", 
    "meetha paan", "maghai paan", "banarasi paan", "calcuttan paan", "supari processing", 
    "split nut", "whole nut", "supari dust", "tobacco dust", "foil laminate", 
    "pouch foil", "packing film", "zipper pouch", "tin packaging", "tobacco flavoring",

    # 5. PROMOTERS, OWNERS & KEY REGIONAL SUSPECTS
    "uday shankar chaurasia", "uday shankar prasad chaurasia", "shree baijnath agencies", 
    "shree baijanathjee and sons", "sikhar distribution guwahati", "dggi guwahati zonal unit", 
    "kishore wadhwani", "vijay kumar nair", "basant makhija", "ratan makhija", 
    "kamlesh chhabria", "praveen punjabi", "amit bothra", "ashok dagar", 
    "rasiklal dhariwal", "dhariwal industries", "jm joshi", "jmj group", 
    "kothari products", "deepak kothari", "jaiprakash kothari", "vishnu essence", 
    "shikhar group", "pradeep agarwal", "aaa enterprises",

    # 6. HAWALA, MONEY LAUNDERING & FINANCIAL CRIME TERMS
    "hawala", "hawala transaction", "money laundering", "pmla", "prevention of money laundering act", 
    "black money", "cash syndicate", "cash courier", "angadia", "angadia service", 
    "shell company", "bogus billing", "fake invoice", "paper firm", "accommodation entry", 
    "unaccounted cash", "clandestine sale", "clandestine clearance", "off the record sales", 
    "cash channel", "border cash movement", "hawala operator", "cash ledger",

    # 7. EXPANDED TAX, GST, CESS & PRICE HIKE TERMS
    "gst", "gst council", "gst hike", "compensation cess", "ad valorem", 
    "tax evasion", "excise duty", "customs duty", "tax fraud", "input tax credit", 
    "itc fraud", "fake invoice", "bogus billing", "e-way bill", "eway bill violation", 
    "evasion detection", "capacity based tax", "track and trace", "qr code tax", 
    "pouch machine tax", "packing machine registration", "form gst pmts", "tax threshold", 
    "gst circular", "cbitc", "cbic", "finance ministry", "tax notification", 
    "cess levy", "tax revision", "tobacco tax", "sin tax", "health cess", 
    "anti evasion", "tax raid", "tax demand", "penalty notice", "confiscation order", 
    "seizure memo", "gst audit", "excise raid", "revenue leakage", "under invoicing", 
    "cash sales", "unreported turnover", "duty evasion", "customs evasion", "tax scam", 
    "price hike", "price revision", "mrp hike", "rsp increase", "hsns cess", "cost revision",

    # 8. TRANSPORTATION, FREIGHT & FUEL COST HIKE TERMS
    "diesel price hike", "fuel price hike", "freight charges", "freight rate hike", 
    "transport fare hike", "truck freight increase", "logistic cost hike", 
    "toll tax hike", "toll fee revision", "fastag rate hike", "fuel surcharge", 
    "truckers strike", "transport association strike", "all india motor transport congress", 
    "aimtc", "transporters union", "truck choke", "wheels off road", "chakka jam", 
    "chicken neck corridor", "siliguri corridor", "guwahati bypass freight", 
    "interstate checkpost freight", "border toll tax", "assam transport union",

    # 9. ENFORCEMENT & INVESTIGATIVE AGENCIES
    "dggi", "directorate general of gst intelligence", "gst intelligence", "cgst", 
    "sgst", "state tax department", "enforcement directorate", "ed", "cbi", 
    "customs", "customs preventive", "revenue intelligence", "dri", "income tax department", 
    "it department", "food safety", "fssai", "food and drug administration", "fda", 
    "police", "crime branch", "special task force", "stf", "anti corruption bureau", 
    "acb", "border security force", "bsf", "assam rifles", "ssb", 
    "cisf", "railway protection force", "rpf", "checkpost", "integrated checkpost", 
    "icp", "sales tax squad", "mobile squad", "flying squad", "dggi guwahati", 
    "dggi kolkata", "dggi delhi", "dggi lucknow", "dggi kanpur", "dggi mumbai", 
    "dggi ahmedabad", "dggi patna", "dggi ranchi", "tax inspector", "customs inspector",

    # 10. REGIONAL LOCATIONS: NORTHEAST INDIA & PAN-INDIA HUBS
    "assam", "guwahati", "beltola", "dispur", "jalukbari", "changsari", 
    "tezpur", "silchar", "jorhat", "dibrugarh", "bongaigaon", "dhubri", 
    "karimganj", "srirampur", "boxirhat", "nagaland", "dimapur", "kohima", 
    "chumuokedima", "mon", "arunachal", "arunachal pradesh", "itanagar", "pasighat", 
    "naharlagun", "mizoram", "aizawl", "zokhawthar", "champhai", "manipur", 
    "imphal", "moreh", "tripura", "agartala", "meghalaya", "shillong", 
    "byrnihat", "khanapara", "jiaganj", "siliguri", "north bengal", "chicken neck", 
    "duars", "dhupguri", "falakata", "cooch behar", "alipurduar", "jalpaiguri", 
    "guwahati zonal unit", "kanpur", "lucknow", "noida", "delhi", "mumbai", "ahmedabad",

    # 11. LOGISTICS, SUPPLY CHAIN & CRACKDOWNS
    "truck", "container", "lorry", "transportation", "transporter", 
    "logistics", "consignment", "shipment", "transit", "cargo", 
    "freight", "warehouse", "godown", "cold storage", "stockyard", 
    "distribution hub", "wholesale market", "distributor", "stockist", "super stockist", 
    "dealer", "trader", "supplier", "clearing agent", "carrying agent", 
    "cnf", "c&f agent", "supply chain", "illicit trade", "smuggling route", 
    "transit check", "vehicle interception", "raid", "search and seizure", "seized", 
    "confiscated", "intercepted", "busted", "sealed", "arrested", "illegal factory"
])

def contains_monitored_keyword(text: str) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in ALL_MONITORED_KEYWORDS)

def is_recent(published_parsed) -> bool:
    if not published_parsed:
        return True  # Fallback if no date tag exists
    
    pub_time = time.mktime(published_parsed)
    now_time = time.time()
    
    # Process only articles published within MAX_AGE_MINUTES
    return (now_time - pub_time) <= (MAX_AGE_MINUTES * 60)

async def check_once():
    bot = Bot(token=TELEGRAM_TOKEN)
    sent_count = 0
    now_ist_str = datetime.now(IST).strftime("%I:%M %p IST (%d %b %Y)")

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                # 1. Filter out older news
                if is_recent(entry.get("published_parsed")):
                    # 2. Check keyword relevance
                    if contains_monitored_keyword(entry.title):
                        message = (
                            f"🚨 **LIVE MARKET / SUPPLY CHAIN ALERT**\n"
                            f"⏰ **Alert Time:** {now_ist_str}\n\n"
                            f"**Headline:** {entry.title}\n"
                            f"**Published:** {entry.get('published', 'Just Now')}\n\n"
                            f"🔗 [Source Link]({entry.link})"
                        )
                        
                        await bot.send_message(
                            chat_id=CHAT_ID,
                            text=message,
                            parse_mode="Markdown"
                        )
                        sent_count += 1
                        print(f"[SENT ALERT]: {entry.title}")
        except Exception as e:
            print(f"[ERROR]: {e}")

    # 3. Heartbeat status message in IST
    if sent_count == 0:
        no_news_msg = (
            
            f"."
        )
        await bot.send_message(
            chat_id=CHAT_ID,
            text=no_news_msg,
            parse_mode="Markdown"
        )
        print("[STATUS SENT]: No new news found.")

if __name__ == "__main__":
    asyncio.run(check_once())
