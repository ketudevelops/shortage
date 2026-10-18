import asyncio
import logging
import feedparser
from telegram import Bot

# ==============================================================================
# CONFIGURATION
# ==============================================================================
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

# Check interval set strictly to 30 seconds
POLL_INTERVAL = 30

# Targeted RSS Feeds
RSS_FEEDS = [
    # 1. DGGI, Customs, Raids & Tax Evasion (Assam, Guwahati, Nagaland, Arunachal, Pan India)
    "https://news.google.com/rss/search?q=DGGI+OR+tax+OR+raid+OR+seized+Assam+OR+Guwahati+OR+Nagaland&hl=en-IN&gl=IN&ceid=IN:en",
    # 2. Major Pan Masala & Gutkha Brands
    "https://news.google.com/rss/search?q=Vimal+OR+Rajnigandha+OR+Pan+Parag+OR+Kamala+Pasand+OR+Shikhar+gutkha&hl=en-IN&gl=IN&ceid=IN:en",
    # 3. Supari & Areca Nut Smuggling (Northeast Corridors)
    "https://news.google.com/rss/search?q=supari+OR+areca+nut+seized+Assam+OR+Mizoram+OR+Nagaland&hl=en-IN&gl=IN&ceid=IN:en",
    # 4. GST Council, Cess & Tobacco Policy
    "https://news.google.com/rss/search?q=GST+Council+tax+hike+tobacco+OR+pan+masala+cess&hl=en-IN&gl=IN&ceid=IN:en",
    # 5. Cigarette, Zarda & Bidi Enforcement
    "https://news.google.com/rss/search?q=illegal+cigarettes+OR+bidi+OR+zarda+seized+India&hl=en-IN&gl=IN&ceid=IN:en"
]

# ==============================================================================
# 500+ KEYWORD DATABASE
# ==============================================================================
ALL_MONITORED_KEYWORDS = set([
    # 1. MAJOR PAN MASALA & GUTKHA BRANDS
    "vimal", "rajnigandha", "pan parag", "rmd", "manikchand", "kamala pasand", 
    "shikhar", "rajshree", "pan bahar", "pan vilas", "goa gutkha", "dilbagh", 
    "tulsi", "baba", "baba 120", "baba 160", "baba elaichi", "pass pass", 
    "chaini khaini", "miraj", "shahi spm", "mubarak", "sir", "aashiqui", 
    "aashiqui gutkha", "tansen", "rounak", "dinesh pouches", "red rose", 
    "jmj", "jmj group", "gagan", "gagan pan masala", "kuber", "kuber gutkha", 
    "golden 17", "ratna 300", "meetha mazaa", "gulab", "dilruba", "shahi gulab", 
    "hans", "hans chhap", "vimal bola", "vimal kesar", "kamla pasand", "shikhar premium",
    "cool lip", "gold mohar", "swagat",

    # 2. TOBACCO, ZARDA, KHAINI & SMOKELESS BRANDS
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

    # 5. REGULATORY, TAXES, GST & POLICY TERMS
    "gst", "gst council", "gst hike", "compensation cess", "ad valorem", 
    "tax evasion", "excise duty", "customs duty", "tax fraud", "input tax credit", 
    "itc fraud", "fake invoice", "bogus billing", "e-way bill", "eway bill violation", 
    "evasion detection", "capacity based tax", "track and trace", "qr code tax", 
    "pouch machine tax", "packing machine registration", "form gst pmts", "tax threshold", 
    "gst circular", "cbitc", "cbic", "finance ministry", "tax notification", 
    "cess levy", "tax revision", "tobacco tax", "sin tax", "health cess", 
    "anti evasion", "tax raid", "tax demand", "penalty notice", "confiscation order", 
    "seizure memo", "gst audit", "excise raid", "revenue leakage", "under invoicing", 
    "cash sales", "unreported turnover", "duty evasion", "customs evasion", "tax scam", "gst scam",

    # 6. ENFORCEMENT & INVESTIGATIVE AGENCIES
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

    # 7. REGIONAL LOCATIONS: NORTHEAST INDIA
    "assam", "guwahati", "beltola", "dispur", "jalukbari", "changsari", 
    "tezpur", "silchar", "jorhat", "dibrugarh", "bongaigaon", "dhubri", 
    "karimganj", "srirampur", "boxirhat", "nagaland", "dimapur", "kohima", 
    "chumuokedima", "mon", "arunachal", "arunachal pradesh", "itanagar", "pasighat", 
    "naharlagun", "mizoram", "aizawl", "zokhawthar", "champhai", "manipur", 
    "imphal", "moreh", "tripura", "agartala", "meghalaya", "shillong", 
    "byrnihat", "khanapara", "jiaganj", "siliguri", "north bengal", "chicken neck", 
    "duars", "dhupguri", "falakata", "cooch behar", "alipurduar", "jalpaiguri", 
    "guwahati zonal unit", "ne border",

    # 8. REGIONAL LOCATIONS: PAN-INDIA HUBS
    "kanpur", "unnao", "lucknow", "noida", "greater noida", "ghaziabad", 
    "varanasi", "prayagraj", "ahmedabad", "surat", "vadodara", "vapi", 
    "rajkot", "indore", "bhopal", "gwalior", "uijain", "patna", 
    "muzaffarpur", "gaya", "ranchi", "jamshedpur", "dhanbad", "cuttack", 
    "bhubaneswar", "kolkata", "howrah", "mumbai", "pune", "thane", 
    "nagpur", "delhi", "delhi ncr", "faridabad", "gurugram", "jaipur", 
    "jodhpur", "bikaner", "raipur", "bilaspur", "hyderabad", "chennai", 
    "bengaluru", "silvassa", "daman", "jammu", "kashipur", "haridwar", "pantnagar",

    # 9. LOGISTICS, SUPPLY CHAIN & TRANSPORTATION
    "truck", "container", "lorry", "transportation", "transporter", 
    "logistics", "consignment", "shipment", "transit", "cargo", 
    "freight", "warehouse", "godown", "cold storage", "stockyard", 
    "distribution hub", "wholesale market", "distributor", "stockist", "super stockist", 
    "dealer", "trader", "supplier", "clearing agent", "carrying agent", 
    "cnf", "c&f agent", "supply chain", "illicit trade", "smuggling route", 
    "transit check", "vehicle interception", "forged invoice", "without eway bill", "fake eway bill", 
    "mislabeled cargo", "hidden compartment", "secret cavity", "unclaimed cargo", "interstate movement", 
    "border crossing", "customs clearance", "railways parcel", "courier shipment", "air cargo", 
    "seaport consignment", "inland container depot", "icd", "transport agency",

    # 10. CRACKDOWNS, ENFORCEMENT & LEGAL TERMINOLOGY
    "raid", "search and seizure", "seized", "confiscated", "intercepted", 
    "busted", "uncovered", "exposed", "sealed", "attached", 
    "detained", "arrested", "apprehended", "interrogated", "booked", 
    "fir registered", "case registered", "show cause notice", "scn", "summons", 
    "illegal factory", "unlicensed unit", "spurious plant", "counterfeit goods", "duplicate pan masala", 
    "fake packaging", "counterfeit gutkha", "unauthorized unit", "clandestine manufacture", "clandestine removal", 
    "secret factory", "underground warehouse", "tax evasion racket", "smuggling syndicate", "cartel", 
    "hawala connection", "cash seizure", "unaccounted cash", "black money", "property attachment", 
    "court order", "ban violation", "cotpa violation", "fssai violation", "illegal operation", 
    "seizure value", "crores seized", "lakhs seized", "enforcement action"
])

# Memory set to avoid duplicate alerts
seen_articles = set()

def contains_monitored_keyword(text: str) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in ALL_MONITORED_KEYWORDS)

async def poll_feeds(bot: Bot):
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                article_url = entry.link
                
                # Check if new item and contains any keyword
                if article_url not in seen_articles:
                    if contains_monitored_keyword(entry.title):
                        seen_articles.add(article_url)
                        
                        message = (
                            f"🚨 **LIVE SUPPLY CHAIN / RAID ALERT**\n\n"
                            f"**Headline:** {entry.title}\n"
                            f"**Published:** {entry.get('published', 'Just Now')}\n\n"
                            f"🔗 [Source Link]({entry.link})"
                        )
                        
                        await bot.send_message(
                            chat_id=CHAT_ID,
                            text=message,
                            parse_mode="Markdown",
                            disable_web_page_preview=False
                        )
                        print(f"[SENT]: {entry.title}")
                    else:
                        # Silently record seen non-matching link to save memory
                        seen_articles.add(article_url)
        except Exception as e:
            # Silent fallback on network issues
            pass

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    print(f"Monitoring active ({len(ALL_MONITORED_KEYWORDS)} keywords). Polling every 30 seconds...")
    
    # Pre-fill seen_articles on startup so old news isn't sent instantly
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                seen_articles.add(entry.link)
        except Exception:
            pass

    print("Startup cache ready. Watching for live breaking updates...")

    while True:
        await poll_feeds(bot)
        await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    asyncio.run(main())
