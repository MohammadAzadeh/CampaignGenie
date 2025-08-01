import json
import requests
import random
import os
import uuid
from typing import Optional

from io import BytesIO
from PIL import Image

import dotenv

dotenv.load_dotenv("app/pages/.env", verbose=True)

ADVERTISER_ID = ""
SESSION_ID = os.getenv("SESSION_ID")
COOKIES = f"sessionid={SESSION_ID}"
ACCOUNT_ID = os.getenv("ACCOUNT_ID")

CATEGORY_MAP = {
    "بیماری و درمان": "IAB287",
    "جراحی و خدمات زیبایی": "IAB323",
    "سبک زندگی سالم": "IAB223",
    "جشن‌ها و مراسمات": "IAB163",
    "موضوعات حساس": "IAB2004",
    "تخفیف و قرعه‌کشی": "IAB473",
    "مراقبت زیبایی و بهداشت فردی": "IAB553",
    "مد و پوشاک": "IAB552",
    "ورزش": "IAB483",
    "خودرو": "IAB1",
    "املاک": "IAB441",
    "مدرسه و کنکور سراسری": "IAB132",
    "کسب و کار": "IAB53",
    "اقتصاد": "IAB80",
    "صنعت و کشاورزی": "IAB90",
    "سرمایه شخصی": "IAB391",
    "تکنولوژی": "IAB596",
    "تجهیزات الکترونیک شخصی": "IAB632",
    "بازی ویدیویی": "IAB680",
    "کتاب و ادبیات": "IAB42",
    "خدمات": "IAB2003",
    "سرگرمی و مهارت و هنر": "IAB239",
    "مذهب": "IAB453",
    "علم و دانش": "IAB464",
    "تفریح": "IAB150",
    "سفر و گردشگری": "IAB653",
    "سینما و تلویزیون و تئاتر": "IAB324",
    "موسیقی": "IAB338",
    "عامه پسند": "IAB432",
    "خانواده": "IAB186",
    "روابط عاطفی": "IAB188",
    "والدین": "IAB192",
    "لوازم و تجهیزات خانه": "IAB274",
    "ساخت و ساز و تغییر دکوراسیون": "IAB276",
    "غذا و نوشیدنی": "IAB210",
    "حیوانات خانگی": "IAB422",
    "زبان آموزی": "IAB147",
    "رمز ارز": "IAB2001",
    "دانشگاه و تحصیلات عالی": "IAB137",
    "اشتغال": "IAB123",
    "مهاجرت": "IAB2002",
    "حقوق": "IAB383",
    "سیاست": "IAB386",
    "اجتماعی": "IAB380",
}

{"image": ["یک عکس معتبر آپلود کنید. فایلی که ارسال کردید عکس یا عکس خراب شده نیست"]}

SEGMENT_MAP = {
    "سفر و گردشگری": 28,
    "خدمات": 51,
    "مذهب": 30,
    "مدرسه و کنکور سراسری": 26,
    "املاک": 44,
    "غذا و نوشیدنی": 9,
    "ساخت و ساز و تغییر دکوراسیون": 55,
    "سرگرمی و مهارت و هنر": 56,
    "دانشگاه و تحصیلات عالی": 53,
    "لوازم و تجهیزات خانه": 61,
    "تفریح": 48,
    "صنعت و کشاورزی": 58,
    "مراقبت زیبایی و بهداشت فردی": 62,
    "کسب و کار": 60,
    "بازی ویدیویی": 45,
    "سینما و تلویزیون و تئاتر": 57,
    "سرمایه شخصی": 18,
    "جراحی و خدمات زیبایی": 49,
    "اشتغال": 42,
    "سبک زندگی سالم": 7,
    "کتاب و ادبیات": 59,
    "والدین": 11,
    "خودرو": 52,
    "زبان آموزی": 54,
    "مد و پوشاک": 15,
    "تجهیزات الکترونیک شخصی": 46,
    "مهاجرت": 29,
    "تخفیف و قرعه\u200cکشی": 47,
    "تکنولوژی": 19,
    "جشن\u200cها و مراسمات": 50,
    "اقتصاد": 43,
}


def refresh_token():
    global HEADERS, ADVERTISER_ID

    response = requests.get(
        url=f"https://accounts.yektanet.com/api/v2/token/access/internal/?account={ACCOUNT_ID}",
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://panel.yektanet.com/",
            "Origin": "https://panel.yektanet.com",
            "Connection": "keep-alive",
            "Cookie": COOKIES,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "TE": "trailers",
        },
    )
    HEADERS = {
        "Authorization": "JWT " + json.loads(response.text)["token"],
        "Cookie": COOKIES,
    }
    response = requests.get(
        "https://api.yektanet.com/api/v2/adv/profile/", headers=HEADERS
    )
    ADVERTISER_ID = json.loads(response.text)["id"]


def create_native_campaign(
    name: str,
    daily_budget: int,
    cost_per_click: int,
    page_keywords: list[str],
    page_categories: list[str],
    user_segments: list[str],
) -> Optional[int]:
    page_categories = [
        category for category in page_categories if category in CATEGORY_MAP
    ]
    user_segments = [segment for segment in user_segments if segment in SEGMENT_MAP]
    refresh_token()
    campaign_creation_request = requests.post(
        url="https://api.yektanet.com/api/v2/adv/campaigns/",
        headers=HEADERS,
        json={
            "title": name,
            "campaign_type": "native",
            "only_re_targeting": False,
            "only_related_content": True,
            "is_keyword": len(page_keywords) > 0,
            "is_category": len(page_categories) > 0,
            "is_audience_sharing": False,
            "is_autotargeting": False,
            "segmentation_selected": len(user_segments) > 0,
            "auto_publishers_select": True,
            "display_publisher_group": "",
            "publishers_visible": True,
            "core_partners": [],
            "is_fixed": False,
            "property_type": None,
            "minimum_interval_between_duplicates": 24,
            "cost_limit": daily_budget,
            "bid": cost_per_click,
            "use_campaign_total_balance": False,
            "bidding_strategy": "cpc",
            "monetization_type": "cpc",
            "utm_campaign": f"adv_{ADVERTISER_ID}_{''.join(random.choices('123456789', k=7))}",
            "utm_medium": "native-targeted",
            "utm_term_status": "محتوا",
            "utm_term": "",
            "utm_content_status": "ناشر",
            "utm_content": "",
            "utm_source": "yektanet",
            "is_daily": False,
            "is_periodic": False,
            "device_os_type": "all",
            "display_all_os_versions": True,
            "display_all_mobile_brands": True,
            "display_mobile_brand": [],
            "display_all_countries": True,
            "countries": [],
            "display_location": [],
            "show_only_in_capital": False,
            "display_in_all_isp": True,
            "display_isp": [
                "Shatel",
                "Iran Cell",
                "Mobile Communication Company",
                "Rightel",
                "Asiatech",
                "Mobin Net",
                "Telecommunication",
                "Pars Online",
                "Afranet",
                "Respina",
                "Information Technology Company",
                "Neda Rayaneh",
                "Other",
            ],
            "publisher_floating_bids": [],
            "publisher_group_floating_bids": [],
            "subcategories": [
                {"category_id": CATEGORY_MAP.get(category), "subcategory_id": 0}
                for category in page_categories
            ],
            "keywords": [{"keyword": keyword} for keyword in page_keywords],
            "negative_keywords": [],
            "broad_allowed": True,
            "goal": {"type": "9", "tags": []},
            "config": {
                "segment_ids": [SEGMENT_MAP.get(segment) for segment in user_segments],
            },
            "segmentation_enabled": len(user_segments) > 0,
            "target_suppliers": ["web", "push"],
            "is_push_supplier_active": True,
            "is_adivery_supplier_active": False,
            "is_divar": False,
            "divar_config": {
                "cities": [],
                "category_slugs": [],
                "categories": [],
                "keywords": [],
                "neighborhoods": [],
                "min_price": None,
                "max_price": None,
                "brands": [],
                "smart_targeting": True,
            },
            "is_rubika": False,
            "user_apply": False,  # Indicates campaign should be active or not
        },
    )
    if campaign_creation_request.status_code != 201:
        print(campaign_creation_request.text, campaign_creation_request.status_code)
        return None
    campaign_id = json.loads(campaign_creation_request.text)["id"]
    print(f"{campaign_id}: Created campaign")
    return campaign_id


def read_and_resize_image(image_path: str) -> BytesIO:
    img = Image.open(image_path)
    max_side = 600
    img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

    image_file = BytesIO()
    img.save(image_file, format="PNG", optimize=True)
    image_file.seek(0)
    return image_file


def create_ad(
    campaign_id: int, ad_title: str, image_path: str, ad_url: str, ad_cta_title: str
):
    image_file = read_and_resize_image(image_path)
    refresh_token()
    print(f"{campaign_id}: Creating ad")
    ad_creation_request = requests.post(
        url="https://ad-management.yektanet.com/v1/ad/",
        headers=HEADERS,
        data={
            "campaign": campaign_id,
            "title": ad_title,
            "item_url": ad_url,
            "description": "",
            "user_apply": "off",  # This indicates that the ad should be active or not
            "cta_color": "#9BD2FF",
            "cta_title": ad_cta_title[:13],
            "image_source": "manual",
        },
        files={"image": ("image.png", image_file, "image/png")},
        timeout=30,
    )
    if ad_creation_request.status_code != 201:
        print(ad_creation_request.text, ad_creation_request.status_code)
        return None
    ad_id = json.loads(ad_creation_request.text)["id"]
    print(f"{campaign_id}: Created ad {ad_id}")
    return ad_id


def generate_ad_image(ad_image_description: str):
    print("Generating image")
    refresh_token()
    image_creation_request = requests.post(
        url="https://assistant.yektanet.com/api/v2/facilitator/assets/images/",
        headers=HEADERS,
        json={
            "raw_prompt": ad_image_description,
            "campaign_id": None,
            "images_count": 1,
            "images_ratio": "3:2",
        },
        timeout=60,
    )
    if image_creation_request.status_code != 201:
        print(image_creation_request.text, image_creation_request.status_code)
        return None
    image_url = json.loads(image_creation_request.text)["images"][0]["image"]
    print(f"Generated image {image_url}")
    print(f"Downloading Image")
    resp = requests.get(image_url, timeout=20)
    resp.raise_for_status()
    img = Image.open(BytesIO(resp.content)).convert("RGB")
    # max_side = 600
    # img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    image_name = uuid.uuid4()
    image_path = f"app/pages/files/static/images/{image_name}.png"
    img.save(image_path, format="PNG", optimize=True)
    print(f"Saved image {image_name}")
    return image_path


if __name__ == "__main__":
    print(
        create_native_campaign(
            name="تست پنج",
            daily_budget=1_000_000,
            cost_per_click=2200,
            page_keywords=["لیفت صورت"],
            page_categories=[],
            user_segments=[],
            ad_title="رزرو ویلای خفن با شب",
            ad_image_description="مردی در حال خوردن چای لب ساحل با خانواده",
            ad_url="https://shab.ir",
            ad_cta_title="رزرو کن!",
        )
    )
