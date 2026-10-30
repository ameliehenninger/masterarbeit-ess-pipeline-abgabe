"""
Phase 3 – Narratives Profil (Technik 1): eine Zeile aus ESS_profil_DE.csv als Fließtext.

Die Person wird in zweiter Person beschrieben ("You are a 42-year-old woman."), in Absätzen ohne
Überschriften. Zusammengehörige Variablen werden zu einem Satz verbunden (Haushalt, Vertrauen in
Institutionen, politische Beteiligung, …), damit ein zusammenhängender Text statt einer Liste entsteht.
Eingesetzt werden nur Werte aus der Profilzeile und Labels aus dem ESS-Codebook – es wird nichts
erfunden. Formulierungen aus Codebook und Erhebungsdesign ("post-coded", "not applicable is recorded",
Split-Ballot-Gruppe, "listed on the card") kommen nicht vor: Der Text enthält nur, was die Person
über sich selbst weiß.

Jede nicht leere Profilvariable (außer den ausgeschlossenen ID-Spalten) wird verwendet. Drei reine
Kodiervariablen ohne eigene Information werden mit ihrer Bezugsvariable verbraucht, ohne eigenen Satz:
    admrclc   Zuweisung zur Fragevariante der Klimafragen (bestimmt nur, welche testjc/testji gefüllt sind)
    dscrnap   "nicht zutreffend"-Markierung, folgt aus dscrgrp = Nein
    medtrnap  "nicht zutreffend"-Markierung, folgt aus medtrun = Nein
Doppelte Kodierungen derselben Angabe werden zu einem Satz zusammengefasst (marsts/maritalb,
mainact/mnactic, rlgdnm/rlgdnade). Variablen ohne Vorlage bekommen einen generischen Satz aus
Codebook-Titel und Antwort-Label.

Platzhalter in den Vorlagen:
    {label}    Antwort-Label laut Codebook            ("Very interested")
    {lc}       Label mit kleinem Anfangsbuchstaben   ("very interested")
    {value}    Zahlenwert                            ("42", "13.2")
    {scale}    Wert auf der Antwortskala             ("8 on a scale from 0 (no trust at all) to 10 (complete trust)")
    {country}  Land der Person laut Codebook         ("Germany")
    {is} {are} {work} {have} {job}   Zeitform für die Arbeit: Gegenwart, wenn die Person in den letzten
                                     7 Tagen bezahlt gearbeitet hat, sonst Vergangenheit ("your last job")
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from ..codebook import parse_variable_texts


@dataclass(frozen=True)
class VariableInfo:
    title: str
    labels: dict[str, str]  # Code -> Label, ohne Missing-Codes


def load_variable_info(missing_codes_csv: str | Path, codebook_html: str | Path) -> dict[str, VariableInfo]:
    """Titel (Codebook) und Antwort-Labels (ESS_missing_codes.csv) je Variable."""
    texts = parse_variable_texts(codebook_html)
    codes = pd.read_csv(missing_codes_csv, dtype=str, keep_default_na=False)
    codes = codes[codes["is_missing"] == "False"]
    labels = {var: dict(zip(g["code"], g["label"], strict=True)) for var, g in codes.groupby("variable")}
    return {var: VariableInfo(lines[0] if lines else var, labels.get(var, {})) for var, lines in texts.items()}


# ---------------------------------------------------------------------------
# Formatierung
# ---------------------------------------------------------------------------

def _lc(s: str) -> str:
    """Ersten Buchstaben klein, außer bei Abkürzungen ("ES-ISCED", "CDU") und "I" ("I have …")."""
    if (len(s) > 1 and s[1].isupper()) or s == "I" or s.startswith(("I ", "I'", "I’")):
        return s
    return s[:1].lower() + s[1:]


def _num(v: str) -> str:
    x = float(v)
    return str(int(x)) if x.is_integer() else f"{x:.4g}"


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def _join(items: list[str], conj: str = "and") -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + f" {conj} " + items[-1]


_PRESENT = {"is": "is", "are": "are", "work": "work", "have": "have", "allow": "allows", "job": "your job"}
_PAST = {"is": "was", "are": "were", "work": "worked", "have": "had", "allow": "allowed", "job": "your last job"}


@dataclass
class Ctx:
    var: str
    value: str
    info: VariableInfo
    country: str
    row: dict[str, str] = field(default_factory=dict)

    @property
    def label(self) -> str | None:
        label = self.info.labels.get(self.value)
        return None if label is None else label.replace("[country]", self.country)

    @property
    def code(self) -> int:
        return int(float(self.value))

    def endpoints(self) -> str:
        """"from 0 (no trust at all) to 10 (complete trust)" """
        numeric = sorted(int(c) for c in self.info.labels if c.isdigit())
        lo, hi = str(numeric[0]), str(numeric[-1])
        lo_label = _lc(self.info.labels[lo].replace("[country]", self.country))
        hi_label = _lc(self.info.labels[hi].replace("[country]", self.country))
        return f"from {lo} ({lo_label}) to {hi} ({hi_label})"

    def scale(self) -> str:
        return f"{_num(self.value)} on a scale {self.endpoints()}"

    @property
    def tense(self) -> dict[str, str]:
        working = self.row.get("pdwrk") == "1" or self.row.get("crpdwk") == "1"
        return _PRESENT if working else _PAST


class _Fields:
    """Liefert Platzhalter erst bei Bedarf; fehlendes Label -> KeyError -> generischer Satz."""

    def __init__(self, ctx: Ctx) -> None:
        self.ctx = ctx

    def __getitem__(self, key: str) -> str:
        c = self.ctx
        if key == "country":
            return c.country
        if key == "value":
            return _num(c.value)
        if key in ("label", "lc"):
            label = c.info.labels[c.value].replace("[country]", c.country)
            return label if key == "label" else _lc(label)
        if key == "scale":
            return c.scale()
        if key in _PRESENT:
            return c.tense[key]
        raise KeyError(key)


def _fmt(template: str, ctx: Ctx) -> str:
    return template.format_map(_Fields(ctx))


def _generic(ctx: Ctx) -> str:
    answer = ctx.label if ctx.label is not None else ctx.value
    return f'Asked about "{ctx.info.title}", your answer was: {answer}.'


# ---------------------------------------------------------------------------
# Vorlagen für eine Variable
# ---------------------------------------------------------------------------

Spec = str | dict[str, str] | Callable[[Ctx], str]


def _render(spec: Spec | None, ctx: Ctx) -> tuple[str, bool]:
    """(Satz, generisch?)"""
    try:
        if callable(spec):
            return spec(ctx), False
        if isinstance(spec, dict):
            tpl = spec.get(ctx.value, spec.get("*"))
            if tpl is not None:
                return _fmt(tpl, ctx), False
        elif isinstance(spec, str):
            return _fmt(spec, ctx), False
    except (KeyError, ValueError, IndexError):
        pass
    return _generic(ctx), True


def yn(yes: str, no: str) -> dict[str, str]:
    return {"1": yes, "2": no}


def marked(yes: str, no: str) -> dict[str, str]:
    return {"1": yes, "0": no}


def _favour(subject: str) -> Callable[[Ctx], str]:
    def f(ctx: Ctx) -> str:
        p = _lc(ctx.info.labels[ctx.value]).replace("in favour nor against", "in favour of nor against")
        if p.endswith("in favour"):
            p += " of"
        return f"You are {p} {subject}."
    return f


def _inprdsc(ctx: Ctx) -> str:
    label = ctx.info.labels[ctx.value]
    if ctx.value == "0":
        return "There is no one with whom you can discuss intimate and personal matters."
    if label == "1":
        return "There is 1 person with whom you can discuss intimate and personal matters."
    return f"There are {label} people with whom you can discuss intimate and personal matters."


_RELIGIOUS_FREQ = {"7": "never", "6": "even less often than only on special holy days"}


# ---------------------------------------------------------------------------
# Vorlagen für mehrere Variablen (ein Satz oder kurzer Absatzteil)
# ---------------------------------------------------------------------------

C = dict[str, Ctx]  # nur die nicht leeren Variablen der Gruppe


@dataclass(frozen=True)
class Group:
    vars: tuple[str, ...]
    render: Callable[[C], str]


def rated(lead: str, items: list[tuple[str, str]]) -> Group:
    """
    Werte auf einer gemeinsamen Skala in einem Satz:
    "On a scale from 0 (no trust at all) to 10 (complete trust), your trust is 4 in …, 8 in … and 7 in …."
    Items mit anderen Skalenenden bekommen einen eigenen Satz.
    """
    def render(c: C) -> str:
        runs: list[tuple[Ctx, list[str]]] = []  # (erste Variable der Skala, Teilsätze)
        for var, phrase in items:
            if var not in c:
                continue
            if not runs or c[var].endpoints() != runs[-1][0].endpoints():
                runs.append((c[var], []))
            runs[-1][1].append(_fmt(phrase, c[var]))
        return " ".join(f"On a scale {x.endpoints()}, {_fmt(lead, x)} {_join(parts)}." for x, parts in runs)
    return Group(tuple(v for v, _ in items), render)


def listed(lead: str, items: list[tuple[str, str]], end: str = "") -> Group:
    """lead + Aufzählung der Teilsätze + end, z. B. "In your opinion, women often …, rarely … and …." """
    def render(c: C) -> str:
        parts = [_fmt(phrase, c[var]) for var, phrase in items if var in c]
        return f"{lead} {_join(parts)}{end}."
    return Group(tuple(v for v, _ in items), render)


def did(lead: str, items: list[tuple[str, str, str]]) -> Group:
    """
    Ja/Nein- bzw. markiert/nicht markiert-Fragen (Code 1 = ja):
    "In the last 12 months you signed a petition and …; you did not wear … or take part in …."
    items = (Variable, Satzteil bei ja, Grundform bei nein)
    """
    def render(c: C) -> str:
        yes = [y for v, y, _ in items if v in c and c[v].value == "1"]
        no = [n for v, _, n in items if v in c and c[v].value != "1"]
        parts = ([_join(yes)] if yes else []) + ([f"did not {_join(no, 'or')}"] if no else [])
        return f"{lead} you " + "; you ".join(parts) + "."
    return Group(tuple(v for v, _, _ in items), render)


def by_label(lead: str, items: list[tuple[str, str]]) -> Group:
    """
    Gleiche Antwort-Labels zusammenfassen:
    "During the past week you were happy and enjoyed life most of the time; you felt sad … some of the time."
    """
    def render(c: C) -> str:
        groups: dict[str, list[str]] = {}
        for var, phrase in items:
            if var in c:
                groups.setdefault(_lc(c[var].label), []).append(phrase)
        return f"{lead} you " + "; you ".join(f"{_join(p)} {lab}" for lab, p in groups.items()) + "."
    return Group(tuple(v for v, _ in items), render)


# --- Über die Person --------------------------------------------------------

def _gender_age(c: C) -> str:
    sex = {"1": "man", "2": "woman"}.get(c["gndr"].value) if "gndr" in c else None
    if sex and "agea" in c:
        age = _num(c["agea"].value)
        article = "an" if age.startswith("8") or age in ("11", "18") else "a"
        return f"You are {article} {age}-year-old {sex}."
    if sex:
        return f"You are a {sex}."
    return f"You are {_num(c['agea'].value)} years old."


_DOMICIL = {"1": "a big city", "2": "the suburbs or outskirts of a big city", "3": "a town or small city",
            "4": "a country village", "5": "a farm or home in the countryside"}


def _residence(c: C) -> str:
    country = c["cntry"].label if "cntry" in c else next(iter(c.values())).country
    where = f"{c['region'].label}, {country}" if "region" in c else country
    if "domicil" in c:
        return f"You live in {_DOMICIL[c['domicil'].value]} in {where}."
    return f"You live in {where}."


def _origin(c: C) -> str:
    country = next(iter(c.values())).country
    parts = []
    if "brncntr" in c:
        if c["brncntr"].value == "1":
            parts.append(f"were born in {country}")
        else:
            parts.append(f"were born in {c['cntbrthd'].label}" if "cntbrthd" in c else f"were born outside {country}")
    elif "cntbrthd" in c:
        parts.append(f"were born in {c['cntbrthd'].label}")
    if "livecnta" in c:
        parts.append(f"first came to live in {country} in {_num(c['livecnta'].value)}")
    if "ctzcntr" in c:
        parts.append(f"{'are' if c['ctzcntr'].value == '1' else 'are not'} a citizen of {country}")
    return f"You {_join(parts)}."


def _languages(c: C) -> str:
    if "lnghom1" in c and "lnghom2" in c:
        return f"At home you mostly speak {c['lnghom1'].label}, and also {c['lnghom2'].label}."
    return f"At home you mostly speak {(c.get('lnghom1') or c['lnghom2']).label}."


def _ancestry_label(ctx: Ctx) -> str:
    # Codebook-Kürzel: "German nfs" (not further specified), "… nec" (not elsewhere classified)
    return re.sub(r"\s+(nfs|nec)$", "", ctx.label)


def _ancestry(c: C) -> str:
    names = [_ancestry_label(c[v]) for v in ("anctrya1", "anctrya2") if v in c]
    return f"You describe your ancestry as {_join(names)}."


def _parents_birth(c: C) -> str:
    country = next(iter(c.values())).country

    def where(born: str, other: str) -> str | None:
        if born in c and c[born].value == "1":
            return country
        if other in c:
            return c[other].label
        if born in c:
            return f"outside {country}"
        return None

    father, mother = where("facntr", "fbrncntc"), where("mocntr", "mbrncntc")
    if father and father == mother:
        return f"Both your parents were born in {father}."
    parts = [f"your father was born in {father}" if father else "",
             f"your mother was born in {mother}" if mother else ""]
    return _cap(_join([p for p in parts if p])) + "."


def _body(c: C) -> str:
    parts = [f"are {_num(c['height'].value)} cm tall" if "height" in c else "",
             f"weigh {_num(c['weighta'].value)} kg" if "weighta" in c else ""]
    return f"You {_join([p for p in parts if p])}."


# --- Haushalt ---------------------------------------------------------------

_MEMBER = {  # Beziehung -> (männlich, weiblich, unbekannt)
    "1": ("your partner", "your partner", "your partner"),
    "2": ("your son", "your daughter", "your child"),
    "3": ("your father or father-in-law", "your mother or mother-in-law", "a parent or parent-in-law of yours"),
    "4": ("your brother", "your sister", "a sibling of yours"),
    "5": ("a male relative", "a female relative", "a relative"),
    "6": ("a man who is not related to you", "a woman who is not related to you", "a person who is not related to you"),
    "": ("another man", "another woman", "another person"),
}


def _member(c: C, n: int) -> str | None:
    rel, sex, year = (c.get(f"rshipa{n}"), c.get(f"gndr{n}"), c.get(f"yrbrn{n}"))
    if not (rel or sex or year):
        return None
    i = {"1": 0, "2": 1}.get(sex.value if sex else "", 2)
    who = _MEMBER[rel.value if rel else ""][i]
    extra = []
    if rel and rel.value == "1" and sex:
        extra.append(("a man", "a woman")[i])
    if year:
        extra.append(f"born {_num(year.value)}")
    return who + (f" ({', '.join(extra)})" if extra else "")


def _household(c: C) -> str:
    members = [m for n in range(2, 7) if (m := _member(c, n))]
    size = int(float(c["hhmmb"].value)) if "hhmmb" in c else len(members) + 1
    if size == 1 and not members:
        return "You live alone."
    if not members:
        return f"Including yourself, {size} people live in your household."
    return f"You live in a household of {size} people: {_join(['you'] + members)}."


_PARTNERSHIP = {
    "1": "You are legally married to the partner you live with.",
    "2": "You are in a legally registered civil union with the partner you live with.",
    "3": "You live with your partner; your relationship is not legally recognised.",
    "4": "You live with your partner; your relationship is legally recognised.",
    "5": "You are legally separated from the partner you live with.",
    "6": "You are legally divorced from the partner you live with, or your civil union was dissolved.",
}
_MARITAL = {
    "1": "You are legally married.", "2": "You are in a legally registered civil union.",
    "3": "You are legally separated.", "4": "You are legally divorced, or your civil union was dissolved.",
    "5": "You are widowed, or your civil partner died.",
    "6": "You have never been married or in a legally registered civil union.",
}


def _partnership(c: C) -> str:
    out = []
    if "rshpsts" in c:
        out.append(_PARTNERSHIP[c["rshpsts"].value])
    # maritalb ist die nachkodierte Fassung von marsts (gleiche Codes) -> ein Satz
    marital = c.get("maritalb") or c.get("marsts")
    same = "rshpsts" in c and c["rshpsts"].value in ("1", "2") and c["rshpsts"].value == (marital and marital.value)
    if marital and not same:
        out.append(_MARITAL[marital.value])
    ever = []
    if "lvgptnea" in c:
        ever.append("lived with a partner without being married to them" if c["lvgptnea"].value == "1"
                    else "never lived with a partner without being married to them")
    if "dvrcdeva" in c:
        ever.append("been divorced or had a civil union dissolved" if c["dvrcdeva"].value == "1"
                    else "never been divorced or had a civil union dissolved")
    if ever:
        out.append(f"You have {_join(ever)}.")
    return " ".join(out)


# --- Bildung und Arbeit -----------------------------------------------------

def _education(c: C, school: str, voc: str, whose: str = "Your") -> list[str]:
    out = []
    if school in c:
        out.append(f"{whose} highest school-leaving qualification is: {c[school].label}.")
    if voc in c:
        out.append(f"{whose} highest vocational or university qualification is: {c[voc].label}.")
    return out


def _own_education(c: C) -> str:
    out = _education(c, "edudde1", "educde2")
    if "eduyrs" in c:
        out.append(f"Altogether you completed {_num(c['eduyrs'].value)} years of full-time education.")
    return " ".join(out)


_ACTIVITY = {"1": "in paid work", "2": "in education", "3": "unemployed and looking for a job",
             "4": "unemployed and not looking for a job", "5": "permanently sick or disabled", "6": "retired",
             "7": "doing community or military service", "8": "doing housework or looking after children or others",
             "9": "doing something else"}


def _activity(c: C) -> str:
    out = []
    main = c.get("mnactic") or c.get("mainact")  # mnactic = nachkodierte Fassung von mainact
    if main:
        out.append(f"In the last 7 days you were mainly {_ACTIVITY[main.value]}.")
        if "mainact" in c and "mnactic" in c and c["mainact"].value != c["mnactic"].value:
            out.append(f"You yourself described it as being {_ACTIVITY[c['mainact'].value]}.")
    main_is_work = main is not None and main.value == "1"
    if "pdwrk" in c and c["pdwrk"].value == "1" and not main_is_work:
        out.append("You also did some paid work in the last 7 days.")
    if "pdwrk" in c and c["pdwrk"].value == "0" and not main_is_work and "crpdwk" not in c:
        out.append("You did no paid work in the last 7 days.")
    if "crpdwk" in c:
        out.append("You did at least one hour of paid work in the last 7 days." if c["crpdwk"].value == "1"
                   else "You did no paid work in the last 7 days, not even for an hour.")
    return " ".join(out)


def _job_history(c: C) -> str:
    if "pdjobev" in c and c["pdjobev"].value == "2":
        return "You have never had a paid job."
    if "pdjobyr" in c:
        return f"You were last in a paid job in {_num(c['pdjobyr'].value)}."
    return "You have had a paid job before, but are not in one now."


_ORG = {"1": "in central or local government",
        "2": "in another part of the public sector (such as education or health)",
        "3": "at a state-owned enterprise", "4": "at a private firm", "6": "at another type of organisation"}


def _employment(c: C) -> str:
    t = next(iter(c.values())).tense
    rel = c["emplrel"].value if "emplrel" in c else ""
    if rel == "2" or ("tporgwk" in c and c["tporgwk"].value == "5"):
        s = f"You {t['are']} self-employed"
        if "emplno" in c:
            n = _num(c["emplno"].value)
            s += " without employees" if n == "0" else f" with {n} employee" + ("" if n == "1" else "s")
    elif rel == "3":
        s = f"You {t['work']} in your own family business"
    elif rel == "1":
        s = f"You {t['are']} an employee"
    else:
        s = f"You {t['work']}"
    if "tporgwk" in c and c["tporgwk"].value in _ORG:
        s += " " + _ORG[c["tporgwk"].value]
    if "nacer2" in c:
        s += f' in the industry "{c["nacer2"].label}"'
    if "estsz" in c:
        s += f", at a workplace with {_lc(c['estsz'].label)} employees"
    return s + "."


def _contract_hours(c: C) -> str:
    t = next(iter(c.values())).tense
    out = []
    if "wrkctra" in c:
        out.append({"1": f"Your employment contract {t['is']} of unlimited duration.",
                    "2": f"Your employment contract {t['is']} of limited duration.",
                    "3": f"You {t['have']} no employment contract."}[c["wrkctra"].value])
    if "wkhct" in c and "wkhtot" in c:
        out.append(f"Your contracted working hours {t['are']} {_num(c['wkhct'].value)} a week; including overtime "
                   f"you normally {t['work']} {_num(c['wkhtot'].value)} hours.")
    elif "wkhct" in c:
        out.append(f"Your contracted working hours {t['are']} {_num(c['wkhct'].value)} a week, excluding overtime.")
    elif "wkhtot" in c:
        out.append(f"Including overtime you normally {t['work']} {_num(c['wkhtot'].value)} hours a week.")
    return " ".join(out)


def _supervision(c: C) -> str:
    t = next(iter(c.values())).tense
    if "njbspv" in c:
        return f"You {t['are']} responsible for supervising {_num(c['njbspv'].value)} people."
    if c["jbspv"].value == "1":
        return f"You {t['are']} responsible for supervising other employees."
    return f"You {t['are']} not responsible for supervising other employees."


def _unemployment(c: C) -> str:
    if "uemp3m" in c and c["uemp3m"].value == "2":
        return "You have never been unemployed and looking for work for more than three months."
    out = ["At some point you have been unemployed and looking for work for more than three months."]
    if "uemp12m" in c:
        out.append("At least one of these periods lasted 12 months or more." if c["uemp12m"].value == "1"
                   else "None of these periods lasted 12 months or more.")
    if "uemp5yr" in c:
        out.append("At least one of them was within the past 5 years." if c["uemp5yr"].value == "1"
                   else "None of them was within the past 5 years.")
    return " ".join(out)


# --- Einkommen, Partner, Eltern ----------------------------------------------

def _income(c: C) -> str:
    out = []
    if "hincsrca" in c:
        out.append(f"Your household's main source of income is {_lc(c['hincsrca'].label)}.")
    if "hinctnta" in c:
        decile = c["hinctnta"].label.split(" - ", 1)[1]
        out.append(f"Its total net income falls into the {decile} of the income distribution in "
                   f"{c['hinctnta'].country} (1st decile = lowest tenth, 10th decile = highest tenth).")
    if "hincfel" in c:
        out.append({"1": "You are living comfortably on your household's present income.",
                    "2": "You are coping on your household's present income.",
                    "3": "You find it difficult to live on your household's present income.",
                    "4": "You find it very difficult to live on your household's present income."}[c["hincfel"].value])
    return " ".join(out)


def _partner(c: C) -> str:
    out = _education(c, "edupdde1", "edupcde2", "Your partner's")
    if "mnactp" in c:
        out.append(f"In the last 7 days your partner was mainly {_ACTIVITY[c['mnactp'].value]}.")
    if "crpdwkp" in c:
        out.append("Your partner did at least one hour of paid work in the last 7 days." if c["crpdwkp"].value == "1"
                   else "Your partner did no paid work in the last 7 days.")
    job = []
    if "emprelp" in c:
        job.append({"1": "is an employee", "2": "is self-employed",
                    "3": "works in their own family business"}[c["emprelp"].value])
    if "isco08p" in c:
        job.append(f"works as: {c['isco08p'].label}")
    if job:
        out.append(f"Your partner {_join(job)}.")
    if "wkhtotp" in c:
        out.append(f"Including overtime, your partner normally works {_num(c['wkhtotp'].value)} hours a week.")
    return " ".join(out)


def _parent(prefix: str, word: str) -> Group:
    """prefix = f/m (Variablennamen), word = father/mother."""
    school, voc = f"edu{prefix}cde1", "edufbde2" if prefix == "f" else "edumbde2"
    status, occ = f"empr{prefix}14", f"occ{prefix}14b"

    def render(c: C) -> str:
        out = _education(c, school, voc, f"Your {word}'s")
        if status in c and c[status].value == "4":
            out.append(f"When you were 14, your {word} was dead or absent.")
        else:
            at14 = []
            if status in c:
                at14.append({"1": "was an employee", "2": "was self-employed",
                             "3": "was not working"}[c[status].value])
            if occ in c:
                at14.append(f"worked in the occupational category: {_lc(c[occ].label)}")
            if at14:
                out.append(f"When you were 14, your {word} {_join(at14)}.")
        return " ".join(out)
    return Group((school, voc, status, occ), render)


def _childhood(c: C) -> str:
    parts = []
    if "cnfpplh" in c:
        parts.append(f"there was {_lc(c['cnfpplh'].label)} serious conflict between the people in your household")
    if "fnsdfml" in c:
        parts.append(f"your family {_lc(c['fnsdfml'].label)} experienced severe financial difficulties")
    return f"When you were growing up, {_join(parts)}."


# --- Medien, Politik, Gesellschaft -------------------------------------------

def _media(c: C) -> str:
    out = []
    if "nwspol" in c:
        out.append(f"On a typical day you spend {_num(c['nwspol'].value)} minutes watching, reading or listening "
                   "to news about politics and current affairs.")
    if "netusoft" in c:
        if c["netusoft"].value == "1":
            out.append("You never use the internet.")
        elif "netustm" in c:
            out.append(f"You use the internet {_lc(c['netusoft'].label)}, about {_num(c['netustm'].value)} minutes "
                       "on a typical day.")
        else:
            out.append(f"You use the internet {_lc(c['netusoft'].label)}.")
    elif "netustm" in c:
        out.append(f"On a typical day you spend {_num(c['netustm'].value)} minutes using the internet.")
    return " ".join(out)


_SAY = {"1": "no", "2": "very little", "3": "some", "4": "a lot of", "5": "a great deal of"}


def _political_system(c: C) -> str:
    parts = []
    if "psppsgva" in c:
        parts.append(f"{_SAY[c['psppsgva'].value]} say in what the government does")
    if "psppipla" in c:
        parts.append(f"{_SAY[c['psppipla'].value]} influence on politics")
    return f"You think the political system in {next(iter(c.values())).country} allows people like you {_join(parts)}."


def _political_ability(c: C) -> str:
    parts = []
    if "actrolga" in c:
        parts.append(f"you consider yourself {_lc(c['actrolga'].label)} to take an active role in a group involved "
                     "with political issues")
    if "cptppola" in c:
        parts.append(f"you are {_lc(c['cptppola'].label)} in your own ability to participate in politics")
    return _cap(_join(parts)) + "."


def _party(ctx: Ctx) -> str:
    return "another party" if ctx.value == "55" else ctx.label


def _vote(c: C) -> str:
    v = c["vote"].value if "vote" in c else "1"
    if v == "2":
        return "You did not vote in the last national election."
    if v == "3":
        return "You were not eligible to vote in the last national election."
    votes = []
    if "prtvgde1" in c:
        votes.append(f"your first vote (Erststimme) to {_party(c['prtvgde1'])}")
    if "prtvgde2" in c:
        votes.append(f"your second vote (Zweitstimme) to {_party(c['prtvgde2'])}")
    return "You voted in the last national election" + (f", giving {_join(votes)}" if votes else "") + "."


def _party_closeness(c: C) -> str:
    if "clsprty" in c and c["clsprty"].value == "2":
        return "There is no particular party you feel closer to than all the others."
    s = (f"The party you feel closest to is {_party(c['prtclgde'])}" if "prtclgde" in c
         else "There is a particular party you feel closer to than all the others")
    if "prtdgcl" in c:
        s += f"; you feel {_lc(c['prtdgcl'].label)} to it"
    return s + "."


_ALLOW = {"1": "many", "2": "some", "3": "a few", "4": "no"}


def _immigration(c: C) -> str:
    groups = [("imsmetn", "people of the same race or ethnic group as most people in {country}"),
              ("imdfetn", "people of a different race or ethnic group"),
              ("impcntr", "people from the poorer countries outside Europe")]
    parts = [f"{_ALLOW[c[v].value]} {_fmt(p, c[v])}" for v, p in groups if v in c]
    return f"You would allow {_join(parts)} to come and live in {next(iter(c.values())).country}."


# --- Religion, Klima, Gesundheit ---------------------------------------------

def _denomination(c: C, intl: str, de: str) -> str:
    name = c[intl].label if intl in c else c[de].label
    if intl in c and de in c and c[de].label != c[intl].label:
        name += f" ({c[de].label})"
    return name


def _religion(c: C) -> str:
    belongs = c["rlgblg"].value if "rlgblg" in c else ("1" if "rlgdnm" in c or "rlgdnade" in c else "2")
    if belongs == "1":
        if "rlgdnm" in c or "rlgdnade" in c:
            return f"You belong to a religion or denomination: {_denomination(c, 'rlgdnm', 'rlgdnade')}."
        return "You consider yourself as belonging to a particular religion or denomination."
    s = "You do not belong to any particular religion or denomination"
    if "rlgblge" in c and c["rlgblge"].value == "2":
        s += ", and you never have"
    elif "rlgdnme" in c or "rlgdeade" in c:
        s += f", but in the past you belonged to: {_denomination(c, 'rlgdnme', 'rlgdeade')}"
    elif "rlgblge" in c:
        s += ", but in the past you belonged to one"
    return s + "."


def _discrimination(c: C) -> str:
    # dscrnap ("Gründe: nicht zutreffend") folgt aus dscrgrp = Nein und trägt keine eigene Information
    if "dscrgrp" not in c:
        return ""
    country = c["dscrgrp"].country
    return (f"You describe yourself as a member of a group that is discriminated against in {country}."
            if c["dscrgrp"].value == "1" else
            f"You do not describe yourself as a member of a group that is discriminated against in {country}.")


_CLIMATE = [
    "climate change would be reduced if large numbers of people limited their energy use",
    "large numbers of people will actually limit their energy use to try to reduce climate change",
    "governments in enough countries will take action that reduces climate change",
]


def _climate_expectations(c: C) -> str:
    """
    testjc34–42 (im Hauptteil) und testji1–9 (gleiche Fragen am Ende des Interviews), je drei
    Antwortformate; admrclc bestimmt nur, welches Format die Person bekam -> kein eigener Satz.
    """
    def numeric(vars_: list[str]) -> str:
        items = [(v, f"that {t} at {{value}}") for v, t in zip(vars_, _CLIMATE, strict=True)]
        return rated("you rate the likelihood", items).render(c)

    def verbal(vars_: list[str]) -> str:
        parts = [f"{_lc(c[v].label)} that {t}" for v, t in zip(vars_, _CLIMATE, strict=True) if v in c]
        return f"You think it is {_join(parts)}." if parts else ""

    def again(s: str) -> str:
        return f"Asked the same questions again later in the interview: {s[0].lower()}{s[1:]}" if s else ""

    jc = [f"testjc{i}" for i in range(34, 43)]
    ji = [f"testji{i}" for i in range(1, 10)]
    first = [numeric(jc[0:3]), verbal(jc[3:6]), numeric(jc[6:9])]
    later = [verbal(ji[0:3]), numeric(ji[3:6]), numeric(ji[6:9])]
    return " ".join(s for s in first + [again(x) for x in later] if s)


def _alcohol(c: C) -> str:
    out = []
    if "alcfreq" in c:
        out.append("In the last 12 months you never had a drink containing alcohol." if c["alcfreq"].value == "7"
                   else f"In the last 12 months you had a drink containing alcohol {_lc(c['alcfreq'].label)}.")
    last = []
    if "alcwkdy" in c:
        last.append(f"on a weekday (Monday to Thursday) you drank {_num(c['alcwkdy'].value)} grams of alcohol")
    if "alcwknd" in c:
        last.append(f"on a weekend day (Friday to Sunday) {_num(c['alcwknd'].value)} grams")
    if last:
        out.append(f"The last time you drank {_join(last)}.")
    if "alcbnge" in c:
        out.append("You never drank a binge-drinking amount on a single occasion in the last 12 months."
                   if c["alcbnge"].value == "5" else
                   f"In the last 12 months you drank a binge-drinking amount on a single occasion "
                   f"{_lc(c['alcbnge'].label)}.")
    return " ".join(out)


def _medical_access(c: C) -> str:
    # medtrnap ("Gründe: nicht zutreffend") folgt aus medtrun = Nein und trägt keine eigene Information
    if "medtrun" in c and c["medtrun"].value == "1":
        return ("In the last 12 months you were at least once unable to get a medical consultation or treatment "
                "you needed.")
    if "medtrnu" in c and c["medtrnu"].value == "2":
        return "In the last 12 months you did not need any medical consultation or treatment."
    if "medtrun" in c or "medtrnu" in c:
        return "In the last 12 months you were always able to get the medical consultation or treatment you needed."
    return ""


def _care(c: C) -> str:
    if "hlpfmly" in c and c["hlpfmly"].value == "2":
        return ("Outside your paid work, you do not spend time looking after or helping family members, friends, "
                "neighbours or others.")
    s = "Outside your paid work, you spend time looking after or helping family members, friends, neighbours or others"
    if "hlpfmhr" in c:
        s += f" ({_lc(c['hlpfmhr'].label)})"
    return s + "."


def _cancer(c: C) -> str:
    v = c["hltprca"].value if "hltprca" in c else "2"
    if v == "3":
        return "You have never had cancer."
    s = "You currently have cancer." if v == "1" else "You have had cancer in the past."
    if "cancfre" in c:
        s = s[:-1] + f" and have been cancer-free for {_lc(c['cancfre'].label)}."
    return s


def _covid(c: C) -> str:
    out = []
    if "respc19a" in c:
        out.append({"1": "Since the start of 2020 you have had coronavirus and tested positive.",
                    "2": "Since the start of 2020 you think you have had coronavirus, but you were not tested or "
                         "did not test positive.",
                    "3": "Since the start of 2020 you have not had coronavirus."}[c["respc19a"].value])
    if "symtc19" in c:
        if c["symtc19"].value == "1":
            still = (" and still have some of them now" if c.get("symtnc19") and c["symtnc19"].value == "1"
                     else " but no longer have them" if "symtnc19" in c else "")
            out.append(f"You had symptoms lasting 3 months or longer{still}.")
        else:
            out.append("You did not have symptoms lasting 3 months or longer.")
    elif "symtnc19" in c:
        out.append("You still have some symptoms now." if c["symtnc19"].value == "1" else "You have no symptoms now.")
    if "vacc19" in c:
        out.append("You have received at least one dose of a vaccine against coronavirus." if c["vacc19"].value == "1"
                   else "You have not received any dose of a vaccine against coronavirus.")
    return " ".join(out)


# ---------------------------------------------------------------------------
# Absätze
# ---------------------------------------------------------------------------

Entry = tuple[str, Spec] | Group


def G(vars_: str, render: Callable[[C], str]) -> Group:
    return Group(tuple(vars_.split()), render)


_HOUSEHOLD = " ".join(f"rshipa{n} gndr{n} yrbrn{n}" for n in range(2, 7))

PARAGRAPHS: list[list[Entry]] = [
    # Person, Herkunft
    [
        G("gndr agea", _gender_age),
        G("cntry region domicil", _residence),
        G("brncntr cntbrthd livecnta ctzcntr", _origin),
        G("lnghom1 lnghom2", _languages),
        ("feethngr", yn("You feel you are part of the same race or ethnic group as most people in {country}.",
                        "You do not feel you are part of the same race or ethnic group as most people in {country}.")),
        G("anctrya1 anctrya2", _ancestry),
        G("facntr fbrncntc mocntr mbrncntc", _parents_birth),
        G("height weighta", _body),
    ],
    # Haushalt und Familie
    [
        G(f"hhmmb {_HOUSEHOLD}", _household),
        G("rshpsts marsts maritalb lvgptnea dvrcdeva", _partnership),
        ("chldhhe", yn("At some point you have had children (your own, step, adopted, foster or a partner's children) "
                       "living in your household.", "You have never had children living in your household.")),
        ("paccnt", marked("Your home has none of the common housing problems such as damp, mould, overcrowding, noise "
                          "or extreme heat or cold.",
                          "Your home has at least one housing problem such as damp, mould, overcrowding, noise or "
                          "extreme heat or cold.")),
    ],
    # Bildung und Arbeit
    [
        G("edudde1 educde2 eduyrs", _own_education),
        ("atncrse", yn("In the last 12 months you took a course or attended a lecture or conference to improve your "
                       "knowledge or skills for work.",
                       "In the last 12 months you did not take any course or attend any lecture or conference to "
                       "improve your knowledge or skills for work.")),
        G("pdwrk crpdwk mainact mnactic", _activity),
        G("pdjobev pdjobyr", _job_history),
        G("emplrel emplno tporgwk nacer2 estsz", _employment),
        ("isco08", "Your occupation {is}: {label}."),
        G("wrkctra wkhct wkhtot", _contract_hours),
        G("jbspv njbspv", _supervision),
        rated("you rate how much the management {allow} you", [
            ("wkdcorga", "to decide how your own daily work is organised at {value}"),
            ("iorgact", "to influence policy decisions about the activities of the organisation at {value}")]),
        ("wrkac6m", yn("In the last 10 years you have done paid work in another country for 6 months or more.",
                       "In the last 10 years you have not done paid work in another country for 6 months or more.")),
        G("uemp3m uemp12m uemp5yr", _unemployment),
        ("mbtru", {"1": "You are currently a member of a trade union or similar organisation.",
                   "2": "You were previously a member of a trade union or similar organisation.",
                   "3": "You have never been a member of a trade union or similar organisation."}),
    ],
    # Einkommen, Partner, Eltern
    [
        G("hincsrca hinctnta hincfel", _income),
        G("edupdde1 edupcde2 mnactp crpdwkp emprelp isco08p wkhtotp", _partner),
        _parent("f", "father"),
        _parent("m", "mother"),
        G("cnfpplh fnsdfml", _childhood),
    ],
    # Medien, Vertrauen, Politik
    [
        G("nwspol netusoft netustm", _media),
        ("ppltrst", "Asked whether most people can be trusted or you can't be too careful, you answer {scale}."),
        ("pplfair", "Asked whether most people would try to take advantage of you or try to be fair, you answer "
                    "{scale}."),
        ("pplhlp", "Asked whether people mostly try to be helpful or mostly look out for themselves, you answer "
                   "{scale}."),
        ("polintr", "You are {lc} in politics."),
        G("psppsgva psppipla", _political_system),
        G("actrolga cptppola", _political_ability),
        rated("your trust is", [
            ("trstprl", "{value} in {country}'s parliament"), ("trstlgl", "{value} in the legal system"),
            ("trstplc", "{value} in the police"), ("trstplt", "{value} in politicians"),
            ("trstprt", "{value} in political parties"), ("trstep", "{value} in the European Parliament"),
            ("trstun", "{value} in the United Nations")]),
        G("vote prtvgde1 prtvgde2", _vote),
        did("In the last 12 months", [
            ("contplt", "contacted a politician, government or local government official",
             "contact a politician, government or local government official"),
            ("donprty", "donated to or participated in a political party or pressure group",
             "donate to or participate in a political party or pressure group"),
            ("badge", "wore or displayed a campaign badge or sticker", "wear or display a campaign badge or sticker"),
            ("sgnptit", "signed a petition", "sign a petition"),
            ("pbldmna", "took part in a public demonstration", "take part in a public demonstration"),
            ("bctprd", "boycotted certain products", "boycott any products"),
            ("pstplonl", "posted or shared something about politics online",
             "post or share anything about politics online"),
            ("volunfp", "volunteered for a not-for-profit or charitable organisation",
             "volunteer for a not-for-profit or charitable organisation")]),
        G("clsprty prtclgde prtdgcl", _party_closeness),
        ("lrscale", "On the political left-right scale you place yourself at {scale}."),
    ],
    # Zufriedenheit und Einstellungen
    [
        rated("your satisfaction is", [
            ("stflife", "{value} with your life as a whole"),
            ("stfeco", "{value} with the present state of the economy in {country}"),
            ("stfgov", "{value} with the way the government of {country} is doing its job"),
            ("stfdem", "{value} with the way democracy works in {country}")]),
        rated("you rate", [("stfedu", "the state of education in {country} nowadays at {value}"),
                           ("stfhlth", "the state of health services in {country} nowadays at {value}")]),
        ("gincdif", "You {lc} that the government should take measures to reduce differences in income levels."),
        ("freehms", "You {lc} that gay men and lesbians should be free to live their own life as they wish."),
        ("hmsfmlsh", 'You {lc} with the statement "If a close family member was a gay man or a lesbian, '
                     'I would feel ashamed."'),
        ("hmsacld", "You {lc} that gay male and lesbian couples should have the same rights to adopt children as "
                    "straight couples."),
        ("euftf", "Asked whether European unification should go further or has already gone too far, your position "
                  "is {scale}."),
        ("vteurmmb", {"1": "In a referendum on EU membership tomorrow, you would vote for {country} to remain a member "
                           "of the European Union.",
                      "2": "In a referendum on EU membership tomorrow, you would vote for {country} to leave the "
                           "European Union.",
                      "33": "In a referendum on EU membership tomorrow, you would submit a blank ballot paper.",
                      "44": "In a referendum on EU membership tomorrow, you would spoil the ballot paper.",
                      "55": "In a referendum on EU membership tomorrow, you would not vote.",
                      "65": "In a referendum on EU membership tomorrow, you would not be eligible to vote."}),
        ("lrnobed", "You {lc} that obedience and respect for authority are the most important values children "
                    "should learn."),
        ("loylead", "You {lc} that what {country} needs most is loyalty towards its leaders."),
        G("imsmetn imdfetn impcntr", _immigration),
        ("imbgeco", "Asked whether immigration is bad or good for {country}'s economy, you answer {scale}."),
        ("imueclt", "Asked whether {country}'s cultural life is undermined or enriched by immigrants, you answer "
                    "{scale}."),
        ("imwbcnt", "Asked whether immigrants make {country} a worse or better place to live, you answer {scale}."),
    ],
    # Wohlbefinden und soziales Leben
    [
        ("happy", "Taking all things together, your happiness is {scale}."),
        ("sclmeet", {"1": "You never meet socially with friends, relatives or work colleagues.",
                     "*": "You meet socially with friends, relatives or work colleagues {lc}."}),
        ("inprdsc", _inprdsc),
        ("sclact", "Compared to other people your age, you take part in social activities {lc}."),
        ("crmvct", yn("You or a member of your household have been the victim of a burglary or assault in the last "
                      "5 years.", "Neither you nor any member of your household has been the victim of a burglary "
                      "or assault in the last 5 years.")),
        ("aesfdrk", "Walking alone in your local area after dark, you feel or would feel {lc}."),
        ("ctrlife", "The control you feel you have over your life in general nowadays is {scale}."),
        rated("you rate your emotional attachment", [("atchctr", "to {country} at {value}"),
                                                     ("atcherp", "to Europe at {value}")]),
    ],
    # Religion und Diskriminierung
    [
        G("rlgblg rlgdnm rlgdnade rlgblge rlgdnme rlgdeade", _religion),
        ("rlgdgr", "Regardless of whether you belong to a particular religion, how religious you are is {scale}."),
        ("rlgatnd", {k: f"Apart from special occasions such as weddings and funerals, you {v} attend religious "
                        "services." for k, v in _RELIGIOUS_FREQ.items()}
                    | {"*": "Apart from special occasions such as weddings and funerals, you attend religious "
                            "services {lc}."}),
        ("pray", {k: f"Apart from when you are at religious services, you {v} pray."
                  for k, v in _RELIGIOUS_FREQ.items()}
                 | {"*": "Apart from when you are at religious services, you pray {lc}."}),
        G("dscrgrp dscrnap", _discrimination),
    ],
    # Klimawandel
    [
        ("ccnthum", {"55": "You don't think climate change is happening.",
                     "*": "You think climate change is caused {lc}."}),
        ("ccrdprs", "The personal responsibility you feel to try to reduce climate change is {scale}."),
        ("wrclmch", "You are {lc} about climate change."),
        G("admrclc " + " ".join(f"testjc{i}" for i in range(34, 43)) + " "
          + " ".join(f"testji{i}" for i in range(1, 10)), _climate_expectations),
    ],
    # Gesundheit und Lebensstil
    [
        ("health", "Your general health is {lc}."),
        ("hlthhmp", {"1": "You are hampered a lot in your daily activities by a longstanding illness, disability, "
                          "infirmity or mental health problem.",
                     "2": "You are hampered to some extent in your daily activities by a longstanding illness, "
                          "disability, infirmity or mental health problem.",
                     "3": "You are not hampered in your daily activities by any longstanding illness, disability, "
                          "infirmity or mental health problem."}),
        ("etfruit", {"7": "You never eat fruit (not counting juice).",
                     "*": "You eat fruit (not counting juice) {lc}."}),
        ("eatveg", {"7": "You never eat vegetables or salad (not counting potatoes).",
                    "*": "You eat vegetables or salad (not counting potatoes) {lc}."}),
        ("dosprt", "On {value} of the last 7 days you walked quickly, did sports or other physical activity for "
                   "30 minutes or longer."),
        ("cgtsmok", {"1": "You smoke daily, 10 or more cigarettes.", "2": "You smoke daily, 9 or fewer cigarettes.",
                     "3": "You smoke, but not every day.", "4": "You don't smoke now, but you used to.",
                     "5": "You have only smoked a few times.", "6": "You have never smoked."}),
        G("alcfreq alcwkdy alcwknd alcbnge", _alcohol),
        did("In the last 12 months", [
            ("dshltgp", "discussed your health with a general practitioner",
             "discuss your health with a general practitioner"),
            ("dshltms", "discussed your health with a medical specialist",
             "discuss your health with a medical specialist")]),
        G("medtrun medtrnap medtrnu", _medical_access),
        G("hlpfmly hlpfmhr", _care),
        ("trhltnt", marked("In the last 12 months you did not use any treatments such as physiotherapy, massage, "
                           "osteopathy, acupuncture, homeopathy or herbal treatment for your own health.",
                           "In the last 12 months you used at least one treatment such as physiotherapy, massage, "
                           "osteopathy, acupuncture, homeopathy or herbal treatment for your own health.")),
        by_label("During the past week", [
            ("fltdpr", "felt depressed"), ("flteeff", "felt that everything you did was an effort"),
            ("slprl", "slept restlessly"), ("wrhpp", "were happy"), ("fltlnl", "felt lonely"),
            ("enjlf", "enjoyed life"), ("fltsd", "felt sad"), ("cldgng", "could not get going")]),
        ("hltprbn", marked("In the last 12 months you have had back or neck pain.",
                           "In the last 12 months you have not had back or neck pain.")),
        G("hltprca cancfre", _cancer),
        G("respc19a symtc19 symtnc19 vacc19", _covid),
    ],
    # Persönlichkeit, Geschlecht, Ansichten über Frauen und Männer
    [
        rated("you rate how well each statement describes you:", [
            ("likrisk", '"I like to take risks" {value}'), ("liklead", '"I like to be a leader" {value}'),
            ("sothnds", "\"I am sensitive to others' needs\" {value}"),
            ("actcomp", '"I act compassionately towards others" {value}')]),
        rated("you rate", [("mascfel", "how masculine you feel at {value}"),
                           ("femifel", "how feminine you feel at {value}"),
                           ("impbemw", "how important being a man or a woman is to the way you think about yourself "
                                       "at {value}")]),
        ("trmedmw", {"1": "You have once been treated unfairly because of your gender when visiting a doctor or "
                          "seeking medical treatment.",
                     "2": "You have been treated unfairly more than once because of your gender when visiting a doctor "
                          "or seeking medical treatment.",
                     "3": "You have never been treated unfairly because of your gender when visiting a doctor or "
                          "seeking medical treatment.",
                     "4": "You have never visited a doctor or sought medical treatment."}),
        ("trwrkmw", {"1": "You have once been treated unfairly because of your gender in hiring, pay or promotion "
                          "at work.",
                     "2": "You have been treated unfairly more than once because of your gender in hiring, pay or "
                          "promotion at work.",
                     "3": "You have never been treated unfairly because of your gender in hiring, pay or promotion "
                          "at work.",
                     "4": "You have never had a job or applied for a job."}),
        ("trplcmw", {"1": "You have once been treated unfairly by the police because of your gender.",
                     "2": "You have been treated unfairly by the police more than once because of your gender.",
                     "3": "You have never been treated unfairly by the police because of your gender.",
                     "4": "You have never had any contact with the police."}),
        ("trmdcnt", "You think that, when seeking medical treatment in {country}, {lc}."),
        ("trwkcnt", "You think that, in hiring, pay or promotions at work in {country}, {lc}."),
        ("trplcnt", "Regarding how the police in {country} treat women and men, you think: {lc}."),
        rated("you rate", [
            ("eqwrkbg", "equal numbers of women and men in paid work at {value}"),
            ("eqpolbg", "equal numbers of women and men in positions of political leadership at {value}"),
            ("eqmgmbg", "equal numbers of women and men in higher management positions at {value}"),
            ("eqpaybg", "women and men receiving equal pay for doing the same work at {value}")]),
        ("eqparep", _favour("a legal measure that requires dividing the number of seats in parliament equally between "
                            "women and men")),
        ("eqparlv", _favour("a legal measure that requires both parents to take equal periods of paid leave to care "
                            "for their newborn child")),
        ("freinsw", _favour("firing employees who make insulting comments to women in the workplace")),
        ("fineqpy", _favour("making businesses pay a fine when they pay men more than women for doing the same work")),
        listed("In your opinion, women", [
            ("wsekpwr", "{lc} seek to gain power by getting control over men"),
            ("weasoff", "{lc} get easily offended"),
            ("wlespdm", "are {lc} paid less than men for the same work in {country}"),
            ("wexashr", "{lc} exaggerate claims of sexual harassment in the workplace")]),
        ("wprtbym", "You {lc} that women should be protected by men."),
        ("wbrgwrm", "You {lc} that women tend to have a better sense of what is right and wrong compared with men."),
    ],
    # Gewichte und Stichprobendesign: in den Daten, im Prompt standardmäßig ausgeschlossen
    # (prompt.exclude_profile_columns). Interview-Metadaten löscht schon die Bereinigung (Schritt 9).
    [
        ("dweight", "Your design weight in the survey data is {value}."),
        ("pspwght", "Your post-stratification weight (including design weight) is {value}."),
        ("pweight", "The population size weight for {country} is {value}."),
        ("anweight", "Your analysis weight is {value}."),
        ("domain", "Your sampling domain is {value}."),
        ("prob", "Your probability of being selected for the survey sample was {value}."),
        ("stratum", "Your sampling stratum is {value}."),
        ("psu", "Your primary sampling unit is {value}."),
    ],
]

def _entry_vars(e: Entry) -> tuple[str, ...]:
    return e.vars if isinstance(e, Group) else (e[0],)


@dataclass
class Persona:
    text: str
    n_sentences: int
    n_words: int
    n_empty: int
    generic: list[str] = field(default_factory=list)  # Variablen mit generischem Satz
    covered: set[str] = field(default_factory=set)    # alle verwendeten (nicht leeren) Variablen


def build_persona(row: dict[str, str], info: dict[str, VariableInfo], exclude: list[str]) -> Persona:
    """
    Fließtext für eine Person. `row` = Profilzeile (Spalte -> Wert als Text, "" = leer),
    `exclude` = Spalten, die nicht in den Text dürfen (ID).
    """
    country = info["cntry"].labels.get(row.get("cntry", ""), row.get("cntry", ""))
    columns = [c for c in row if c not in exclude]
    templated = {v for para in PARAGRAPHS for e in para for v in _entry_vars(e)}
    paragraphs_spec = PARAGRAPHS + [[(c, None) for c in columns if c not in templated]]

    def ctx(var: str) -> Ctx:
        return Ctx(var, row[var].strip(), info.get(var, VariableInfo(var, {})), country, row)

    paragraphs: list[str] = []
    generic: list[str] = []
    covered: set[str] = set()
    n_empty = 0
    for para in paragraphs_spec:
        sentences = []
        for e in para:
            present = [v for v in _entry_vars(e) if v in columns and row[v].strip() != ""]
            n_empty += sum(1 for v in _entry_vars(e) if v in columns and row[v].strip() == "")
            if not present:
                continue
            covered |= set(present)
            if isinstance(e, Group):
                c = {v: ctx(v) for v in present}
                try:
                    text = e.render(c)
                except (KeyError, ValueError, IndexError, AttributeError):
                    text = " ".join(_generic(x) for x in c.values())
                    generic += present
            else:
                text, is_generic = _render(e[1], ctx(e[0]))
                if is_generic:
                    generic.append(e[0])
            if text:
                sentences.append(text)
        if sentences:
            paragraphs.append(" ".join(sentences))
    text = re.sub(r"(?<!\.)\.\.(?!\.)", ".", "\n\n".join(paragraphs))  # Label endet auf "etc." + Satzpunkt
    n_sentences = len(re.findall(r"[.!?](?:\"|')?(?=\s|$)", text))
    return Persona(text, n_sentences, len(text.split()), n_empty, generic, covered)
