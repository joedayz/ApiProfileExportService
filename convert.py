import uno
import os
from com.sun.star.beans import PropertyValue
from com.sun.star.connection import NoConnectException
import math
import secretary
import json
from PIL import Image, ImageOps, ImageDraw
import requests
from io import BytesIO
from tempfile import TemporaryFile
from datetime import datetime
from dateutil.parser import parse

months_en = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December"
]

months_no = [
    "",
    "January",
    "Februar",
    "Mars",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Desember"
]


# Three letter month names
short_months_en = list(map(lambda x: x[:3], months_en))
short_months_no = list(map(lambda x: x[:3], months_no))

# engine needed so that we can setup a media loader
engine = secretary.Renderer()

# Media loader can't take arguments, so we store profile on top level.
profile = None


class DocumentConversionException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


def absolute_url(relativeFile):
    """Constructs absolute path to the current dir in the format required by
    PyUNO that working with files"""
    return "file:///" + os.path.realpath(".") + "/" + relativeFile


def export(filename):
    """Handles exporting odt template files to pdf using libreoffice uno"""
    localContext = uno.getComponentContext()
    resolver = localContext.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver",
        localContext
    )
    try:
        context = resolver.resolve(
            "uno:socket,host=0.0.0.0,port=2002;urp;StarOffice.ComponentContext"  # noqa: E501
        )
    except NoConnectException:
        raise DocumentConversionException(
            "Failed to connect to LibreOffice on port %s" % "2002")

    desktop = context.ServiceManager.createInstanceWithContext(
        "com.sun.star.frame.Desktop",
        context
    )
    file = desktop.loadComponentFromURL(
        "file:///tmp/cvtmp.odt",
        "_blank", 0, ())

    output_props = (
        PropertyValue(Name="FilterName", Value="writer_pdf_Export"),
        PropertyValue(Name="Overwrite", Value=True)
    )
    file.storeToURL(absolute_url("./" + filename), output_props)
    file.dispose()


def code_to_country(profile):
    """We only track country code in employment, so this function converts code
    to full name"""
    countries = open("./data/countries.json")
    countries = json.load(countries)
    country_code = profile.get("countryCode")
    country = countries.get(country_code)
    if country_code and country:
        profile["country"] = country["name"]
    else:
        profile["country"] = country_code


def format_from_date(frommonth, fromyear):
    language = profile.get("language")
    short_months = short_months_en if language == "en" else short_months_no
    if frommonth == 0 and fromyear > 0:
        return f'{fromyear}'
    elif frommonth > 0 and fromyear > 0:
        frommonth = short_months[frommonth]
        return f'{frommonth}. {fromyear}'
    elif frommonth > 0 and fromyear == 0:
        return "Invalid"


def format_to_date(tomonth, toyear, lang):
    untilNow = ("present", "inntil nå")[lang == "no"]
    language = profile.get("language")
    short_months = short_months_en if language == "en" else short_months_no
    if (tomonth == 0 and toyear == 0) or (tomonth > 0 and toyear == 0):
        return untilNow
    elif (toyear > 0 and tomonth == 0):
        return f'{toyear}'
    elif (toyear > 0 and tomonth > 0):
        tomonth = short_months[tomonth]
        return f'{tomonth}. {toyear}'


def format_to_year(toyear, lang):
    untilNow = ("present", "inntil nå")[lang == "no"]
    if (toyear == 0):
        return untilNow
    elif (toyear > 0):
        return f'{toyear}'


def format_dates(profile, key):
    """Formates dates in profile to a more human readble format"""
    language = profile.get("language")
    for entry in profile.get(key):
        frommonth = entry.get("frommonth")
        fromyear = entry.get("fromyear")
        toyear = entry.get("toyear")
        tomonth = entry.get("tomonth")
        formatted_from = format_from_date(frommonth, fromyear)
        formatted_to = format_to_date(tomonth, toyear, language)
        formatted_toyear = format_to_year(toyear, language)
        entry["formattedDate"] = f'{formatted_from} - {formatted_to}'
        entry["formattedYear"] = f'{fromyear} - {formatted_toyear}'


def get_name(x):
    if type(x) is dict:
        return x.get("name")


def collect_skills(profile):
    # language = profile.get("language")
    if 'expertise' in profile:
        for exp in profile["expertise"]:
            if 'skillscore_references' in exp:
                skills = list(map(get_name, exp["skillscore_references"]))
                if skills:
                    exp["skills"] = skills
                # else:
                #     if language == "no":
                #         exp["skills"] = ["Ingen ferdigheter funnet"]
                #     else:
                #         exp["skills"] = ["No skills found"]
    if 'experience' in profile:
        for exp in profile["experience"]:
            if 'skillscore_references' in exp:
                skills = list(map(get_name, exp["skillscore_references"]))
                if skills:
                    exp["skills"] = skills
                # else:
                #     if language == "no":
                #         exp["skills"] = ["Ingen ferdigheter funnet"]
                #     else:
                #         exp["skills"] = ["No skills found"]


def collect_language(profile):
    if 'additionaljsonproperties' in profile:
        props = profile["additionaljsonproperties"]
        if isinstance(props, str):
            props = json.loads(props)
        if 'language' in props:
            profile["language"] = props["language"]
        else:
            profile["language"] = "en"


def collect_phone(profile):
    language = profile.get("language")
    phone = profile.get("phone")
    if not phone:
        if language == "no":
            profile["phone"] = "Skjult eller udefinert"
        else:
            profile["phone"] = "Hidden or undefined"


def collect_mail(profile):
    language = profile.get("language")
    mail = profile.get("mail")
    if not mail:
        if language == "no":
            profile["mail"] = "Skjult eller udefinert"
        else:
            profile["mail"] = "Hidden or undefined"


def get_sortv(entry):
    fy = entry.get("fromyear")
    fm = entry.get("frommonth")
    if fy and fm and fy > 0 and fm > 0:
        return (fy, fm)
    else:
        return (-1, -1)


def sort_sections(profile):
    if "education" in profile:
        profile["education"].sort(key=get_sortv, reverse=True)
    if "experience" in profile:
        profile["experience"].sort(key=get_sortv, reverse=True)
    if "employer" in profile:
        profile["employer"].sort(key=get_sortv, reverse=True)


def collect_location(profile):
    language = profile.get("language")
    streetAddress = profile.get("streetAddress")
    postalCode = profile.get("postalCode")
    city = profile.get("city")
    region = profile.get("region")
    profile["location"] = ""
    if streetAddress and postalCode and city and region:
        profile["location"] += streetAddress + ", "
        profile["location"] += postalCode + ", "
        profile["location"] += city + ", "
        profile["location"] += region
    else:
        if language == "no":
            profile["location"] = "Skjult eller udefinert"
        else:
            profile["location"] = "Hidden or undefined"


def translate_personalia(profile):
    language = profile.get("language")
    if language == "en":
        profile["title"] = profile.get("title_en")
        profile["description"] = profile.get("description_en")


def translate_employment(profile):
    language = profile.get("language")
    if language == "en":
        for emp in profile["employer"]:
            emp["company"] = emp.get("company_en")
            emp["title"] = emp.get("title_en")
            emp["description"] = emp.get("description_en")


def translate_experience(profile):
    language = profile.get("language")
    if language == "en":
        for exp in profile["experience"]:
            exp["company"] = exp.get("company_en")
            exp["title"] = exp.get("title_en")
            exp["description"] = exp.get("description_en")


def translate_expertise(profile):
    language = profile.get("language")
    if language == "en":
        for exp in profile["expertise"]:
            exp["title"] = exp.get("title_en")


def translate_education(profile):
    language = profile.get("language")
    if language == "en":
        for edu in profile["education"]:
            edu["fieldOfStudy"] = edu.get("fieldOfStudy_en")
            edu["description"] = edu.get("description_en")
            edu["school"] = edu.get("school_en")


def translate_other(profile):
    language = profile.get("language")
    if language == "en":
        for oth in profile["other"]:
            oth["data"] = oth.get("data_en")
            oth["title"] = oth.get("title_en")


def split_name(profile):
    """Split profile name into fist and last name components"""
    name = profile.get("name")
    split = name.split()
    first_name = " ".join(split[:-1])
    profile["last_name"] = split[-1]
    profile["first_name"] = first_name


def calc_age(profile):
    """Split profile name into fist and last name components"""
    bd_field = profile.get("birthdate")
    language = profile.get("language")
    if (bd_field):
        try:
            date = parse(bd_field)
            now = datetime.now()
            age = now - date
            years = math.floor(age.days / 365.25)

            if language == "no":
                profile["age"] = "{age} år".format(age=years)
            else:
                profile["age"] = "{age} years old".format(age=years)
        except ValueError:
            profile["age"] = "Invalid birthday"
    else:
        profile["age"] = "Age not known"


def calc_created(skill):
    created = skill.get("createdDate")
    if created:
        try:
            return parse(created).year
        except ValueError:
            return "N/A"
    else:
        return "N/A"


def calc_since(profile, skill):
    experience_list = profile.get("experience")
    experience_ref = skill.get("experience")
    if experience_list and experience_ref:
        filtered = list(filter(lambda exp: exp.get("id") in experience_ref,
                               experience_list))

        filtered.sort(key=get_sortv)
        first = next(iter(filtered), None)
        if first:
            year = first.get("fromyear")
            if year:
                return year

    return "N/A"


def parse_score(profile):
    """Parse score, and create computed values that are attached to profile
    totalScore: computed total score of expertise
    starScore: level converted from 1-100 -> 1-5
    starList: array of a number per star in starScore"""
    for exp in profile["expertise"]:
        level = 0
        skillscore_refs = exp.get("skillscore_references")
        if skillscore_refs:
            for ref in skillscore_refs:
                lvl = int(ref.get("level"))
                level += lvl
                star = int((lvl / 100) * 5)
                stars = []
                for x in range(star):
                    stars.append(x + 1)
                ref["starList"] = stars
                ref["starScore"] = int(star)
                ref["since"] = calc_since(profile, ref)
            if level != 0:
                total_score = int(level / len(skillscore_refs))
                exp["totalScore"] = total_score

    copy = profile.get("expertise").copy()
    copy.sort(key=lambda exp: exp.get("totalScore") or 0, reverse=True)
    for c in copy:
        if c.get("skillscore_references"):
            c.get("skillscore_references").sort(
                    key=lambda exp: exp.get("starScore") or 0, reverse=True)
    profile["highlights"] = copy


def massage_data(profile):
    """Do any extra data manipulation before rendering"""
    collect_language(profile)
    translate_personalia(profile)
    translate_employment(profile)
    translate_experience(profile)
    translate_expertise(profile)
    translate_education(profile)
    translate_other(profile)
    collect_skills(profile)
    code_to_country(profile)
    collect_location(profile)
    collect_phone(profile)
    split_name(profile)
    calc_age(profile)
    collect_mail(profile)
    format_dates(profile, "employer")
    format_dates(profile, "education")
    format_dates(profile, "experience")
    sort_sections(profile)
    parse_score(profile)


@engine.media_loader
def images_loader(value, *args, **kwargs):

    border_opt = kwargs.get("border")
    if profile.get("image"):
        response = requests.get(profile.get("image"))
        file = BytesIO(response.content)
        image = Image.open(file)
        mime_type = image.get_format_mimetype()
    else:
        file = open("templates/assets/avatar_square.png", "rb")
        mime_type = "image/png"
        image = Image.open(file).convert("RGB")

    # handle rounded images
    if kwargs.get("rounded"):
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + image.size, fill=255)
        output = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
        output.putalpha(mask)
        tmp = TemporaryFile()
        output.save(tmp, "PNG")
        tmp.seek(0)
        return (tmp, mime_type)
    elif border_opt:
        output = ImageOps.expand(image, border=20, fill=border_opt)
        tmp = TemporaryFile()
        output.save(tmp, "PNG")
        tmp.seek(0)
        return (tmp, mime_type)
    else:
        return (file, mime_type)


def render(payload, template):
    """Render the data to a temporary odt file, all template variables
    resolved"""
    document = {
        'datetime': datetime.now(),
    }
    massage_data(profile)
    result = engine.render(template, **profile, document=document)
    output = open("/tmp/cvtmp.odt", 'wb')
    output.write(result)


def output(payload, template, filename="output.pdf"):
    """Main interface"""
    global profile
    profile = payload
    render(payload, template)
    export(filename)
