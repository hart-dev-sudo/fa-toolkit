#!/usr/bin/env python3
"""
============================================================
          AMERICAN AIRLINES FA PAY CALCULATOR
                     2024 APFA CBA
                         v1.1.1
  Cross-platform: Windows PowerShell 7+ & Mac/Linux Terminal
============================================================
"""

import os
import sys
from datetime import date

# ── Native ANSI colors (no pip install needed) ───────────
# Works on PowerShell 7+ and Mac/Linux terminal natively
class C:
    CYAN    = "\033[96m"
    YELLOW  = "\033[93m"
    GREEN   = "\033[92m"
    RED     = "\033[91m"
    WHITE   = "\033[97m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RESET   = "\033[0m"

def c(color, text):
    return f"{color}{text}{C.RESET}"

# ── Terminal helpers ──────────────────────────────────────
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def hr(char="═", width=65):
    print(c(C.CYAN, char * width))

def header(title):
    hr()
    print(c(C.YELLOW + C.BOLD, f"{'  ' + title:^65}"))
    hr()


# ── Session monthly estimate store ───────────────────────
# Resets on exit nothing is saved between sessions
monthly_estimate = {
    "trips":        [],   # list of trip result dicts
    "contract_start": None,
    "contract_end":   None,
    "hourly_rate":    None,
}

ADVANCE_HOURS = 37.5   # CBA Section 3.O.2 contractually fixed

# ── CBA Data ─────────────────────────────────────────────
PAY_SCALE_BASE = {
     1: 35.82,  2: 37.97,  3: 40.40,  4: 43.03,  5: 47.39,
     6: 53.67,  7: 59.21,  8: 61.11,  9: 62.80, 10: 65.15,
    11: 66.94, 12: 70.12, 13: 82.24,
}

CBA_DATES = [
    (date(2024, 10, 1), 1.0000),
    (date(2025, 10, 1), 1.0275),
    (date(2026, 10, 1), 1.0275 * 1.03),
    (date(2027, 10, 1), 1.0275 * 1.03**2),
    (date(2028, 10, 1), 1.0275 * 1.03**2 * 1.035),
]

PER_DIEM_RATES = {
    date(2024, 10, 1): {"domestic": 2.85, "international": 3.40},
    date(2025, 10, 1): {"domestic": 2.90, "international": 3.45},
    date(2026, 10, 1): {"domestic": 2.95, "international": 3.50},
    date(2027, 10, 1): {"domestic": 3.00, "international": 3.55},
    date(2028, 10, 1): {"domestic": 3.05, "international": 3.60},
}

INTL_OVERRIDE = {"nipd": 3.00, "ipd": 3.75}

BOARDING_TIMES = {
    "dom_narrowbody_small": 35,   # <161 seats  (A319/A320 rare on domestic)
    "dom_narrowbody_large": 40,   # 161+ seats  (ALL 738/MAX8 Oasis, A321-family)
    "dom_widebody":         40,   # B777, B787
    "nipd":                 45,
    "ipd":                  50,
}

# ── Core functions ────────────────────────────────────────
def get_current_cba():
    today = date.today()
    result = CBA_DATES[0]
    for entry in CBA_DATES:
        if today >= entry[0]:
            result = entry
    d, mult = result
    return mult, d.strftime("%B %d, %Y")

def get_rate(yos):
    mult, _ = get_current_cba()
    year = min(max(int(yos), 1), 13)
    return round(PAY_SCALE_BASE[year] * mult, 2)

def get_current_per_diem():
    today = date.today()
    result = PER_DIEM_RATES[date(2024, 10, 1)]
    for d in sorted(PER_DIEM_RATES.keys()):
        if today >= d:
            result = PER_DIEM_RATES[d]
    return result

# ── Quit sentinel ────────────────────────────────────────
class QuitToMenu(Exception):
    pass

def check_quit(raw):
    if raw.lower() in ("q", "quit"):
        print(c(C.YELLOW, "   Open seatbelts! Get out! Leave everything!"))
        raise QuitToMenu()

# ── Input helpers ─────────────────────────────────────────
def parse_time(prompt, default=None):
    """Accept HH:MM or decimal. Returns float hours. q/quit → main menu."""
    dflt = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"{prompt}{dflt}: ").strip()
        check_quit(raw)
        if raw == "" and default is not None:
            return float(default)
        try:
            if ":" in raw:
                h, m = raw.split(":")
                return int(h) + int(m) / 60.0
            return float(raw)
        except (ValueError, IndexError):
            print(c(C.RED, "   [!] Use HH:MM or decimal (e.g. 18:04 or 18.07)"))

def parse_int(prompt, default=None, min_val=0):
    """q/quit → main menu."""
    dflt = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"{prompt}{dflt}: ").strip()
        check_quit(raw)
        if raw == "" and default is not None:
            return default
        try:
            val = int(raw)
            if val >= min_val:
                return val
            print(c(C.RED, f"   [!] Enter a number >= {min_val}"))
        except ValueError:
            print(c(C.RED, "   [!] Enter a whole number leave everything else behind"))

def parse_float(prompt, default=None, min_val=0.0):
    """q/quit → main menu."""
    dflt = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"{prompt}{dflt}: ").strip()
        check_quit(raw)
        if raw == "" and default is not None:
            return default
        try:
            val = float(raw)
            if val >= min_val:
                return val
            print(c(C.RED, f"   [!] Enter a value >= {min_val}"))
        except ValueError:
            print(c(C.RED, "   [!] Invalid leave everything and try again"))

def parse_yes_no(prompt, default="n"):
    """q/quit → main menu."""
    opts = "Y/n" if default.lower() == "y" else "y/N"
    while True:
        raw = input(f"{prompt} ({opts}): ").strip().lower()
        check_quit(raw)
        if raw == "":
            return default.lower() == "y"
        if raw in ("y", "yes"): return True
        if raw in ("n", "no"):  return False
        print(c(C.RED, "   [!] Enter y or n"))

# ── Reference tables ──────────────────────────────────────
def view_pay_scale():
    clear()
    header("2024 APFA PAY SCALE   Section 3.A")
    mults = [m for _, m in CBA_DATES]
    dates = [d.strftime("%m/%d/%y") for d, _ in CBA_DATES]

    print(c(C.WHITE, f"  {'Year':<12}" + "".join(f" {dt:>10}" for dt in dates)))
    hr("─")
    mult_now, lbl_now = get_current_cba()
    for yr in range(1, 14):
        sfx = "st" if yr==1 else "nd" if yr==2 else "rd" if yr==3 else "th"
        row = f"  {yr}{sfx} Year".ljust(12)
        for i, m in enumerate(mults):
            rate = round(PAY_SCALE_BASE[yr] * m, 2)
            cell = f" ${rate:>8.2f}"
            # Highlight the currently active column
            if CBA_DATES[i][0] == next(d for d, m2 in reversed(CBA_DATES) if date.today() >= d):
                row += c(C.GREEN, cell)
            else:
                row += cell
        print(row)
    hr()
    print(c(C.DIM, "  Lineholder guarantee: 71 hrs/month  |  Reserve: 75 hrs/month"))
    print(c(C.GREEN, f"  Active rate period: {lbl_now}"))
    input(c(C.CYAN, "\n  Jump and slide press Enter to return to menu..."))

def view_per_diem():
    clear()
    header("PER DIEM RATES   Section 4.A")
    print(c(C.WHITE, f"  {'Effective Date':<20} {'Domestic':>10} {'International':>15}"))
    hr("─")
    today = date.today()
    current_key = max(k for k in PER_DIEM_RATES if today >= k)
    for d in sorted(PER_DIEM_RATES.keys()):
        rates = PER_DIEM_RATES[d]
        label = d.strftime("%B %d, %Y")
        marker = c(C.GREEN, "  ← current") if d == current_key else ""
        print(f"  {label:<20} ${rates['domestic']:>8.2f}      ${rates['international']:>8.2f}{marker}")
    hr()
    print(c(C.CYAN, "  Per diem is TAX-FREE"))
    print(c(C.DIM,  "  Accrues from sign-in at base (1hr dom / 1hr15 intl) to 15 min after block-in"))
    input(c(C.CYAN, "\n  Step out press Enter to return to menu..."))

# ── Calculator ────────────────────────────────────────────
def run_calculator():
    clear()
    mult, cba_date = get_current_cba()
    pd = get_current_per_diem()

    header("FA TRIP PAY CALCULATOR")
    print(c(C.GREEN, f"   Active CBA rates: {cba_date}"))
    print(c(C.DIM,   "   Type q at any prompt to return to the main menu.\n"))

    # ── Step 1: Rate ──
    print(c(C.WHITE, "  STEP 1 YOUR PAY RATE\n"))
    # Pre-fill from session if available
    session_rate = monthly_estimate["hourly_rate"]
    if session_rate:
        print(c(C.DIM, f"   Session rate on file: ${session_rate:.2f}/hr"))
        print(c(C.DIM,  "   Press Enter to use it, or type a new rate/year.\n"))
    else:
        print(c(C.DIM,   "   Enter your hourly rate, your year of service,"))
        print(c(C.DIM,   "   or press Enter to view the full pay scale.\n"))
    raw = input("   Hourly rate or year of service: ").strip()

    if raw:
        try:
            val = float(raw)
            # If it looks like a year (1-13), treat as YOS; otherwise treat as rate
            if val == int(val) and 1 <= int(val) <= 13:
                yos = int(val)
                rate = get_rate(yos)
                yr = min(yos, 13)
                sfx = "st" if yr==1 else "nd" if yr==2 else "rd" if yr==3 else "th"
                print(c(C.GREEN, f"   → ${rate:.2f}/hr  ({yr}{sfx} year @ {cba_date})\n"))
            else:
                rate = val
                print(c(C.GREEN, f"   → Using ${rate:.2f}/hr\n"))
        except ValueError:
            print(c(C.RED, "   [!] Invalid pulling up the pay scale"))
            raw = ""

    if not raw and session_rate:
        rate = session_rate
        print(c(C.GREEN, f"   → Using session rate ${rate:.2f}/hr\n"))
    elif not raw:
        # Show inline pay scale table, then prompt for year
        mult_now, _ = get_current_cba()
        print()
        print(c(C.CYAN, "  ─" * 32))
        print(c(C.YELLOW, f"  {'Year':<14}" + f"{'Current Rate':>12}" + f"  (@ {cba_date})"))
        print(c(C.CYAN, "  ─" * 32))
        for yr in range(1, 14):
            sfx = "st" if yr==1 else "nd" if yr==2 else "rd" if yr==3 else "th"
            r = round(PAY_SCALE_BASE[yr] * mult_now, 2)
            label = f"  {yr}{sfx} Year"
            print(f"{label:<16}  ${r:.2f}/hr")
        print(c(C.CYAN, "  ─" * 32))
        print()
        yos = parse_int("   Enter your year of service", default=None, min_val=1)
        rate = get_rate(yos)
        yr = min(yos, 13)
        sfx = "st" if yr==1 else "nd" if yr==2 else "rd" if yr==3 else "th"
        print(c(C.GREEN, f"   → ${rate:.2f}/hr  ({yr}{sfx} year @ {cba_date})\n"))

    # ── Step 2: Trip details ──
    print(c(C.WHITE, "  STEP 2 TRIP DETAILS\n"))
    credit = parse_time("   Credit hours  (e.g. 18:04 or 18.07)")
    tafb   = parse_time("   TAFB hours    (e.g. 55:54 or 55.90)")
    legs   = parse_int( "   Number of legs", default=4, min_val=1)

    # ── Step 3: Route type ──
    print(c(C.WHITE, "\n  STEP 3 ROUTE TYPE\n"))
    print("   1. Domestic")
    print(f"   2. NIPD  (Non-Intl Premium Dest. ${INTL_OVERRIDE['nipd']:.2f}/hr override)")
    print(f"   3. IPD   (Intl Premium Dest. ${INTL_OVERRIDE['ipd']:.2f}/hr override)")
    while True:
        rc = input("   Select (1–3): ").strip()
        check_quit(rc)
        if rc in ("1","2","3"):
            route = ["domestic","nipd","ipd"][int(rc)-1]
            break
        print(c(C.RED, "   [!] Enter 1, 2, or 3"))

    # ── Step 4: Boarding ──
    print(c(C.WHITE, "\n  STEP 4 BOARDING PAY  (Section 3.D)\n"))
    print(c(C.DIM, "   Current boarding times (AA flex executed, Section 11.M):"))
    print(c(C.DIM, "     IPD  (any aircraft)                        50 min"))
    print(c(C.DIM, "     NIPD (any aircraft)                        45 min"))
    print(c(C.DIM, "     DOM  161+ seats (ALL 738/MAX8, A321-fam, WB) 40 min"))
    print(c(C.DIM, "     DOM  <161 seats (A319/A320)                  35 min"))

    if route == "ipd":
        default_board = 50
        ac_key = None
    elif route == "nipd":
        default_board = 45
        ac_key = None
    else:
        print()
        print("   Aircraft type (CBA 11.M trigger is SEAT COUNT, not tail):")
        print("     1. 161+ seats   (B737-800/MAX8, A321/A321T/XLR)  40 min")
        print("     2. Widebody     (B777, B787)                     40 min")
        print("     3. <161 seats   (A319/A320)                       35 min")
        print(c(C.DIM, "   Note: every AA 737-800/MAX8 is 172-seat Oasis config → 40 min"))
        while True:
            ac = input("   Select (1–3) [1]: ").strip()
            check_quit(ac)
            if ac == "":
                ac = "1"
            if ac in ("1","2","3"):
                break
            print(c(C.RED, "   [!] Enter 1, 2, or 3"))
        ac_key = ["narrowbody_large","widebody","narrowbody_small"][int(ac)-1]
        default_board = BOARDING_TIMES[f"dom_{ac_key}"]

    print(c(C.GREEN, f"   → Boarding time: {default_board} min  (press Enter to confirm, or type to override)"))
    board_min = parse_int("   Confirm or override", default=default_board, min_val=1)

    # ── Step 5: Extras ──
    print(c(C.WHITE, "\n  STEP 5 RIGS & EXTRAS  (optional)\n"))

    trip_rig = parse_yes_no("   Apply trip rig?  1:3.5 TAFB Section 11.D.4", default="n")

    sit_rig = False
    sit_excess = 0.0
    if parse_yes_no("   Apply sit rig?  >2:30 between flights Section 11.D.6", default="n"):
        sit_rig = True
        print(c(C.DIM, "   Enter sit time ABOVE the 2:30 threshold"))
        print(c(C.DIM, "   (e.g. if actual sit = 4:00, enter 1:30)"))
        sit_excess = parse_time("   Excess sit hours", default=0.0)

    position = 0.0
    if parse_yes_no("   Add position premium?  Section 3.C", default="n"):
        print()
        print(c(C.DIM, "   Common rates:"))
        print(c(C.DIM, "     Lead DOM (NB/A321XLR/B77/B78)  $3.25/hr"))
        print(c(C.DIM, "     Lead NIPD (B77/B78)            $6.50/hr"))
        print(c(C.DIM, "     Purser IPD (B77/B78)           $7.50/hr"))
        print(c(C.DIM, "     Galley (A321XLR/B77/B78)       $1.00–$2.00/hr"))
        position = parse_float("   Position premium $/hr", default=3.25, min_val=0.0)

    # ── Calculate ──
    print()
    print(c(C.DIM, "   Brace for impact! Brace for impact! Brace for impact!"))

    flight_pay   = credit * rate
    intl_pay     = credit * INTL_OVERRIDE.get(route, 0) if route in ("nipd","ipd") else 0.0
    board_hrs    = (legs * board_min) / 60.0
    boarding_pay = board_hrs * (rate / 2.0)
    pd_type      = "international" if route in ("nipd","ipd") else "domestic"
    pd_rate      = pd[pd_type]
    per_diem     = tafb * pd_rate
    rig_credit   = max(0.0, tafb / 3.5 - credit)
    trip_rig_pay = rig_credit * rate if trip_rig else 0.0
    sit_pay      = (sit_excess / 2.0) * rate if sit_rig else 0.0
    position_pay = position * credit
    total        = flight_pay + intl_pay + boarding_pay + per_diem + trip_rig_pay + sit_pay + position_pay

    # ── Results ──
    clear()
    header("TRIP PAY SUMMARY")

    # Two-column layout: NAME(16) + DETAIL(flexible) truncated to LBL, AMT fixed
    # Every $ sign lands in the same column regardless of detail length
    AMT  = 10   # amount field width
    NAME = 16   # row name width
    DTL  = 28   # detail width name+detail = 44 total label chars

    def result_line(name, detail, amount, note=""):
        note_str = c(C.DIM, f"  {note}") if note else ""
        # Truncate detail if over DTL so amount column never shifts
        detail_fmt = detail[:DTL] if len(detail) > DTL else detail
        label = f"{name:<{NAME}}{detail_fmt:<{DTL}}"
        print(f"  {label}  {c(C.WHITE, f'${amount:>{AMT},.2f}')}{note_str}")

    result_line(
        "Flight Pay",
        f"{credit:.2f} hrs @ ${rate:.2f}",
        flight_pay
    )
    if intl_pay > 0:
        result_line(
            "Intl Override",
            f"{credit:.2f} hrs @ ${INTL_OVERRIDE[route]:.2f} ({route.upper()})",
            intl_pay
        )
    result_line(
        "Boarding Pay",
        f"{legs} legs x {board_min} min @ ${rate/2:.2f}/hr",
        boarding_pay,
        f"({board_hrs:.2f} hrs)"
    )
    result_line(
        "Per Diem",
        f"{tafb:.2f} TAFB hrs @ ${pd_rate:.2f}/hr",
        per_diem,
        "tax-free"
    )
    if trip_rig_pay > 0:
        result_line(
            "Trip Rig",
            f"+{rig_credit:.2f} credit hrs @ ${rate:.2f}",
            trip_rig_pay
        )
    if sit_pay > 0:
        result_line(
            "Sit Rig",
            f"{sit_excess:.2f} excess hrs / 2 @ ${rate:.2f}",
            sit_pay
        )
    if position_pay > 0:
        result_line(
            "Position Prem",
            f"{credit:.2f} hrs @ ${position:.2f}/hr",
            position_pay
        )

    TOTAL_LBL = NAME + DTL
    hr("─")
    print(f"  {'ESTIMATED GROSS PAY':<{TOTAL_LBL}}  {c(C.GREEN + C.BOLD, f'${total:>{AMT},.2f}')}")
    print(c(C.CYAN, "  Per diem is tax-free your taxable total is lower"))
    hr()
    print(c(C.DIM, "  Jump and slide!"))

    # ── Add to monthly estimate? ──
    print()
    add = parse_yes_no("  Add this trip to your monthly estimate?", default="n")
    if add:
        monthly_estimate["trips"].append({
            "flight_pay":   flight_pay,
            "intl_pay":     intl_pay,
            "boarding_pay": boarding_pay,
            "per_diem":     per_diem,
            "trip_rig_pay": trip_rig_pay,
            "sit_pay":      sit_pay,
            "position_pay": position_pay,
            "total":        total,
            "taxable":      flight_pay + intl_pay + boarding_pay + trip_rig_pay + sit_pay + position_pay,
            "rate":         rate,
            "credit":       credit,
        })
        if monthly_estimate["hourly_rate"] is None:
            monthly_estimate["hourly_rate"] = rate
        n = len(monthly_estimate["trips"])
        print(c(C.GREEN, f"  Added. You have {n} trip{'s' if n != 1 else ''} in your monthly estimate."))


# ── Contract glossary ─────────────────────────────────────

def _gloss_pay_system():
    clear()
    header("AA PAY SYSTEM   Section 3.O")
    rate = monthly_estimate["hourly_rate"] or get_rate(7)
    advance = round(ADVANCE_HOURS * rate, 2)
    print(f"""
  HOW AA PAYS YOU

  You get two checks per month one at the end of the
  month (the advance) and one mid-month (the balance).
  It sounds backwards because it kind of is.

  ── END OF MONTH CHECK  (pays on the 30th) ──────────
  This is your ADVANCE for the NEXT contract month.
  AA pays you 37.5 hours at your hourly rate upfront,
  regardless of how much you actually fly that month.

  Why 37.5 hours? It's half the reserve guarantee
  (75 hrs). It's contractually fixed. CBA Section 3.O.2.

  This check contains only the advance no trip
  earnings, no per diem. Taxes and deductions apply.

  e.g. At 7th year rate ($60.84/hr):
    37.5 x $60.84 = $2,281.50 advance gross
    (taxes and deductions reduce your net from there)

  ── MID-MONTH CHECK  (pays on the 15th) ─────────────
  This is where all your actual trip earnings land.
  The advance from the previous month gets clawed
  back first, but this check typically comes out
  ahead trip earnings, boarding pay, rigs, and
  per diem all stack here.

  Your mid-month gross:
    All trip earnings for the contract month
    MINUS the advance recovery from last month
    = Earnings after advance

  Per diem shows up as a separate non-taxable
  line item (F/A EXP - D Non-Taxable on your stub).
  Only the per diem portion is tax-free the rest
  of your earnings are taxed normally.

  ── CONTRACT MONTH ───────────────────────────────────
  AA's contract month is not always a clean calendar
  month. AA publishes adjusted month dates annually
  before vacation bids. Check your pay statement 
  it's listed at the top as "Contract Month."

  ── LIGHT MONTH? ─────────────────────────────────────
  If you flew a light month, your trip earnings might
  barely cover the advance recovery, leaving little
  net on the 15th. That's expected the advance
  went out early on the 30th. The money was already
  paid, just earlier.

  ── PAY DATES ────────────────────────────────────────
  30th advance (or preceding business day if weekend)
  15th balance (or following business day if weekend)
  February advance pays on the 28th

  For full details, reference CBA Section 3.O.
""")
    _gloss_pause()

def view_glossary():
    while True:
        clear()
        header("CONTRACT GLOSSARY & PAY REFERENCE")
        print(c(C.DIM, "  Plain English. No legalese. CBA sections noted.\n"))
        print("   1.  Credit Hours")
        print("   2.  TAFB  (Time Away From Base)")
        print("   3.  Per Diem")
        print("   4.  Boarding Pay")
        print("   5.  Trip Rig  ← includes worked example")
        print("   6.  Sit Rig   ← includes worked example")
        print("   7.  Lineholder & Reserve Guarantees")
        print("   8.  Position Premiums  (Lead / Purser / Galley)")
        print("   9.  NIPD & IPD  (International Override Pay)")
        print("  10.  AA Pay System  (advance, mid-month, EOM)")
        print(c(C.DIM, "   Enter  Return to main menu\n"))

        choice = input("   Select → ").strip().lower()

        if choice in ("q", "quit", ""):
            return
        elif choice == "1":
            _gloss_credit()
        elif choice == "2":
            _gloss_tafb()
        elif choice == "3":
            _gloss_perdiem()
        elif choice == "4":
            _gloss_boarding()
        elif choice == "5":
            _gloss_trip_rig()
        elif choice == "6":
            _gloss_sit_rig()
        elif choice == "7":
            _gloss_guarantee()
        elif choice == "8":
            _gloss_position()
        elif choice == "9":
            _gloss_intl()
        elif choice == "10":
            _gloss_pay_system()
        else:
            print(c(C.RED, "   [!] Enter 1-10 or press Enter to return"))

def _gloss_pause():
    input(c(C.CYAN, "\n  Press Enter to return to glossary..."))

def _gloss_credit():
    clear()
    header("CREDIT HOURS   Section 3.A")
    print("""
  Credit hours are the foundation of your flight pay.

  The clock starts when the parking brake is released
  (chocks out) at departure and stops when the parking
  brake is set (chocks in) at arrival. This is block
  time not wheels up to wheels down, not door to door.

  Your trip paperwork (QIK/SABRE) shows credit hours
  already calculated. This is the number you enter
  into the calculator.

  e.g. ORD → DFW  brake release 08:02, brake set 10:19
       Credit = 2 hrs 17 min  (2:17 or 2.28)

  For full details and exceptions, reference CBA Section 3.A.
""")
    _gloss_pause()

def _gloss_tafb():
    clear()
    header("TAFB TIME AWAY FROM BASE   Section 4.A")
    print("""
  TAFB is how long you're away from your home base.
  It's used to calculate your per diem NOT your
  flight pay.

  The clock starts at sign-in time for your outbound
  flight at your base:
    Domestic:      1 hour before scheduled departure
    International: 1 hour 15 min before scheduled departure

  The clock stops at the end of your debrief period
  after blocking in at your base on the return:
    Domestic:      15 minutes after block in
    IPD:           30 minutes after block in

  Your trip paperwork shows TAFB already calculated.
  It's the number next to "TAFB" on your sequence.

  e.g. Sign-in ORD Monday 07:02  (1 hr before 08:02 departure)
       Block in ORD Wednesday 16:29 + 15 min debrief
       TAFB = approx 56:57 hrs

  For full details and exceptions, reference CBA Section 4.A.
""")
    _gloss_pause()

def _gloss_perdiem():
    clear()
    header("PER DIEM   Section 4.A")
    print(f"""
  Per diem is your meal and incidental expense money.
  It's paid for every hour you're away from base
  (your TAFB hours).

  Current rates:
    Domestic:       ${get_current_per_diem()["domestic"]:.2f} per hour
    International:  ${get_current_per_diem()["international"]:.2f} per hour

  THE BEST PART: Per diem is largely TAX-FREE.
  It's not reported as income in most cases. Every
  dollar of per diem is a dollar you keep unlike
  your flight pay which gets taxed like regular income.

  CAVEAT: There are exceptions particularly on
  single-day trips. If tax treatment of your per diem
  matters for your situation, consult a tax professional
  or reference the CBA directly.

  e.g. Domestic 3-day trip:
       TAFB = 56.90 hrs
       56.90 x $2.90 = $165.01  tax-free in most cases

  For full details and exceptions, reference CBA Section 4.A.
""")
    _gloss_pause()

def _gloss_boarding():
    clear()
    header("BOARDING PAY   Section 3.D")
    print("""
  You get paid for boarding time even though it doesn't
  count as credit hours toward your flight pay.

  The rate is 50% of your hourly rate.
  The time used is the published scheduled boarding
  time per leg NOT actual boarding time.

  Current published boarding times (AA flex executed):
    IPD flights (any aircraft)          50 min/leg
    NIPD flights (any aircraft)         45 min/leg
    DOM widebody / 161+ seats           40 min/leg
    DOM narrowbody <161 seats           35 min/leg

  Example (4-leg domestic A321 trip, 7th year FA):
    e.g. 7th year FA, 4-leg A321 domestic:
         Rate: $60.84/hr   Boarding rate: $30.42/hr
         4 legs x 40 min = 160 min = 2.67 hrs
         2.67 x $30.42 = $81.22 boarding pay

  Note: There are edge case exceptions to boarding pay
  (standby FAs, irregular operations, etc.).
  For full details and exceptions, reference CBA Section 3.D
  and boarding times Section 11.M.
""")
    _gloss_pause()

def _gloss_trip_rig():
    clear()
    header("TRIP RIG   Section 11.D.4")
    print("""
  WHAT IS IT?
  A trip rig is a pay protection rule. It guarantees
  you earn at least 1 hour of pay for every 3.5 hours
  you're away from base (TAFB).

  WHY DOES IT EXIST?
  Without it, a company could schedule you on a trip
  with tons of sit time and very little actual flying.
  You'd be away from home for days but barely get paid.
  The rig prevents that.

  HOW IT WORKS:
  Divide your TAFB by 3.5. If that number is bigger
  than your credit hours, you get paid the difference.
  If your credit hours are already higher, the rig
  doesn't kick in you're already above the floor.

  WORKED EXAMPLE:
  You just finished a 3-day trip. Here's what happened:

    Credit hours:  14:22  (14.37 hrs of actual flying)
    TAFB:          61:45  (61.75 hrs away from base)

  Step 1 Calculate your rig floor:
    61.75 hrs TAFB ÷ 3.5 = 17.64 hrs

  Step 2 Compare to your credit hours:
    Rig floor:    17.64 hrs
    Credit hours: 14.37 hrs
    Difference:    3.27 hrs  ← you're under the floor

  Step 3 Get paid the difference:
    3.27 hrs x your hourly rate = trip rig pay

  At 7th year ($60.84/hr):
    3.27 x $60.84 = $198.95 in trip rig pay

  That 3.27 hours also gets added to your credit total
  for the trip, which counts toward your monthly guarantee.

  If your credit hours had been 18+ hrs, the rig would
  not have triggered at all you were already above
  the 17.64 hr floor.

  CBA Reference: Section 11.D.4
""")
    _gloss_pause()

def _gloss_sit_rig():
    clear()
    header("SIT RIG   Section 11.D.6")
    print("""
  WHAT IS IT?
  A sit rig pays you when you have a long stopover
  between flights on the same duty day. If a stopover
  exceeds 2 hours 30 minutes, you get paid half your
  hourly rate for the time beyond that threshold.

  Quick terminology check:
    Stopover = same-day sit between flights (this applies)
    Layover  = overnight off-duty period (does NOT apply)

  NOTE: Sit rigs are per-stopover, not per-trip. Each
  stopover on a trip is evaluated separately.

  HOW IT WORKS:
  Any stopover time over 2:30 earns 50% of your hourly
  rate. The first 2:30 is not paid only the excess.

  WORKED EXAMPLE:
  You're on a 2-day trip. Between your second and third
  flights you have a 4-hour stopover at DFW.

    Actual stopover:    4:00  (4.00 hrs)
    Free threshold:     2:30  (2.50 hrs)
    Eligible excess:    1:30  (1.50 hrs)  ← only this gets paid

  At 7th year ($60.84/hr), sit rig rate = 50%:
    1.50 hrs x ($60.84 ÷ 2) = 1.50 x $30.42 = $45.63

  So you earned an extra $45.63 for that long stopover.

  IMPORTANT: Sit rig does NOT add credit hours.
  It's additional pay only. Your credit hours stay
  the same only your paycheck goes up.

  For full details and exceptions, reference CBA Section 11.D.6.
""")
    _gloss_pause()

def _gloss_guarantee():
    clear()
    header("MONTHLY GUARANTEES   Section 3.A / 11.C")
    print("""
  The contract guarantees you a minimum number of
  credit hours paid each month, regardless of how
  little you actually fly.

  LINEHOLDER GUARANTEE:  71 hours/month
  If your scheduled trips credit less than 71 hours,
  AA pays you as if you flew 71 hours anyway.
  Most lineholders fly more than this the guarantee
  is a floor, not a target.

  RESERVE GUARANTEE:  75 hours/month
  Reserve FAs get a slightly higher floor because
  they're on call and have less schedule control.
  You get paid 75 hours minimum even if you sit
  reserve all month and never get called out.

  Note: These guarantees are for PAY purposes.
  They don't affect your per diem you only earn
  per diem for trips you actually fly.

  Reserve scheduling has additional rules, thresholds,
  and protections beyond what's covered here.
  For full details and exceptions, reference CBA
  Section 3.A and Section 11.C.
""")
    _gloss_pause()

def _gloss_position():
    clear()
    header("POSITION PREMIUMS   Section 3.C")
    print("""
  Certain positions on a flight earn extra pay on top
  of your base hourly rate. These are paid per credit
  hour, same as your base rate.

  LEAD FA (Domestic narrowbody, A321XLR, B777, B787):
    + $3.25/hr on top of your hourly rate

  LEAD FA (B777 or B787, NIPD route):
    + $6.50/hr on top of your hourly rate

  PURSER (B777 or B787, IPD route):
    + $7.50/hr on top of your hourly rate

  GALLEY (A321XLR, B777, B787):
    + $1.00 to $2.00/hr depending on aircraft

  Example (Lead on a domestic A321XLR, 7th year):
    e.g. Lead on domestic A321XLR, 7th year:
         Base rate:        $60.84/hr
         Lead premium:   + $ 3.25/hr
         Effective rate:   $64.09/hr

         18.07 credit hrs x $64.09 = $1,158.11 flight pay
         vs. $1,099.38 without the premium
         Difference: $58.73 extra for the trip

  CBA Reference: Section 3.C
""")
    _gloss_pause()

def _gloss_intl():
    clear()
    header("NIPD & IPD INTERNATIONAL OVERRIDE   Section 3.G")
    print(f"""
  When you fly international routes, you earn an
  additional override pay on top of your base hourly
  rate. This is paid per credit hour.

  There are two tiers:

  NIPD Non-International Premium Destination:
    Routes like CUN, NAS, GDL, SJO, SJU, etc.
    Override: + $3.00/hr on every credit hour

  IPD International Premium Destination:
    Routes like LHR, CDG, NRT, GRU, HKG, etc.
    Override: + $3.75/hr on every credit hour

  TWO SEPARATE THINGS HAPPENING AT ONCE:

  1. The override pay stacks ON TOP of your base
     hourly rate and is calculated on credit hours.

  2. Your per diem also gets the higher international
     rate but that's completely separate from the
     override. Per diem is still just TAFB x rate.

  So on an international trip you get:
    - Higher flight pay  (base + override x credit hrs)
    - Higher per diem    (intl rate x TAFB hrs)
    These are two different buckets. Neither affects
    how the other is calculated.

  Example (IPD, 7th year, 9:45 credit, 28:00 TAFB):
    e.g. 7th year, 9:45 credit, 28:00 TAFB:
    Base flight pay:   9.75 x $60.84        = $593.19
    IPD override:      9.75 x $ 3.75        = $ 36.56
    Per diem:         28.00 x ${get_current_per_diem()["international"]:.2f}        = $ {28.0 * get_current_per_diem()["international"]:.2f}
    Total:                                    ${9.75*60.84 + 9.75*3.75 + 28.0*get_current_per_diem()["international"]:.2f}

  For full details and exceptions, reference CBA Section 3.G.
""")
    _gloss_pause()


# ── Monthly estimate ──────────────────────────────────────
def view_monthly_estimate():
    clear()
    header("MONTHLY PAY ESTIMATE")

    if not monthly_estimate["trips"]:
        print(c(C.YELLOW, "\n  No trips added yet."))
        print(c(C.DIM,    "  Calculate a trip and choose to add it to your monthly estimate.\n"))
        input(c(C.CYAN,   "  Press Enter to return to menu..."))
        return

    mult, cba_lbl = get_current_cba()
    rate = monthly_estimate["hourly_rate"] or 0.0
    advance_gross = round(ADVANCE_HOURS * rate, 2)

    # Contract month dates
    if not monthly_estimate["contract_start"]:
        print(c(C.DIM, "\n  Enter your contract month dates (shown on your pay statement)."))
        print(c(C.DIM, "  Example: start 06/02  end 07/01\n"))
        monthly_estimate["contract_start"] = input("  Contract month start (MM/DD): ").strip() or ""
        monthly_estimate["contract_end"]   = input("  Contract month end   (MM/DD): ").strip() or ""

    cs = monthly_estimate["contract_start"]
    ce = monthly_estimate["contract_end"]

    # Accumulate totals
    total_flight   = sum(t["flight_pay"]   for t in monthly_estimate["trips"])
    total_intl     = sum(t["intl_pay"]     for t in monthly_estimate["trips"])
    total_boarding = sum(t["boarding_pay"] for t in monthly_estimate["trips"])
    total_perdiem  = sum(t["per_diem"]     for t in monthly_estimate["trips"])
    total_rig      = sum(t["trip_rig_pay"] for t in monthly_estimate["trips"])
    total_sit      = sum(t["sit_pay"]      for t in monthly_estimate["trips"])
    total_position = sum(t["position_pay"] for t in monthly_estimate["trips"])
    total_taxable  = sum(t["taxable"]      for t in monthly_estimate["trips"])
    total_all      = sum(t["total"]        for t in monthly_estimate["trips"])

    AMT  = 10
    NAME = 16
    DTL  = 28
    TOTAL_LBL = NAME + DTL

    def mline(name, detail, amount, note=""):
        note_str = c(C.DIM, f"  {note}") if note else ""
        detail_fmt = detail[:DTL] if len(detail) > DTL else detail
        label = f"{name:<{NAME}}{detail_fmt:<{DTL}}"
        print(f"  {label}  {c(C.WHITE, f'${amount:>{AMT},.2f}')}{note_str}")

    n = len(monthly_estimate["trips"])
    print(c(C.GREEN, f"\n  Contract month: {cs} {ce}"))
    print(c(C.DIM,   f"  {n} trip{'s' if n != 1 else ''} entered this session\n"))

    hr("─")
    print(c(C.WHITE, "  TRIP EARNINGS BREAKDOWN"))
    hr("─")

    mline("Flight Pay",   f"{sum(t['credit'] for t in monthly_estimate['trips']):.2f} hrs total", total_flight)
    if total_intl > 0:
        mline("Intl Override", "accumulated", total_intl)
    mline("Boarding Pay", "accumulated", total_boarding)
    mline("Per Diem",     "accumulated", total_perdiem, "tax-free")
    if total_rig > 0:
        mline("Trip Rig",  "accumulated", total_rig)
    if total_sit > 0:
        mline("Sit Rig",   "accumulated", total_sit)
    if total_position > 0:
        mline("Position",  "accumulated", total_position)

    hr("─")
    print(f"  {'TOTAL TRIP EARNINGS':<{TOTAL_LBL}}  {c(C.WHITE, f'${total_all:>{AMT},.2f}')}")
    print()

    # Mid-month check estimate
    hr("─")
    print(c(C.WHITE, "  PROJECTED MID-MONTH CHECK  (pays ~15th)"))
    hr("─")
    print(c(C.DIM,   "  All trip earnings minus advance recovery"))
    print()
    mline("Trip Earnings", "gross total", total_all)
    mline("Adv Recovery", f"37.5 hrs @ ${rate:.2f}", -advance_gross, "clawed back")
    mid_gross = total_all - advance_gross
    hr("─")
    print(f"  {'ESTIMATED MID-MONTH GROSS':<{TOTAL_LBL}}  {c(C.GREEN + C.BOLD, f'${mid_gross:>{AMT},.2f}')}")
    print(c(C.DIM, f"  Taxable portion: ${total_taxable:,.2f}  |  Tax-free per diem: ${total_perdiem:,.2f}"))
    print()

    # EOM advance estimate
    hr("─")
    print(c(C.WHITE, "  PROJECTED END-OF-MONTH ADVANCE  (pays ~30th)"))
    hr("─")
    print(c(C.DIM,   "  CBA Section 3.O.2 37.5 hrs x your hourly rate"))
    print()
    mline("Advance Pay", f"37.5 hrs @ ${rate:.2f}", advance_gross)
    hr("─")
    print(f"  {'ESTIMATED EOM GROSS':<{TOTAL_LBL}}  {c(C.GREEN + C.BOLD, f'${advance_gross:>{AMT},.2f}')}")
    print(c(C.DIM,   "  Taxes and deductions will reduce your net deduction"))
    print(c(C.DIM,   "  calculator coming in a future version."))
    print()
    hr()
    print(c(C.DIM, "  These are GROSS estimates. Taxes, benefits, 401k,"))
    print(c(C.DIM, "  loans and other deductions will reduce your net pay."))
    print(c(C.DIM, "  For deductions reference your most recent pay statement."))
    hr()

    print()
    try:
        clear_it = parse_yes_no("  Clear monthly estimate and start fresh?", default="n")
        if clear_it:
            monthly_estimate["trips"].clear()
            monthly_estimate["contract_start"] = None
            monthly_estimate["contract_end"]   = None
            monthly_estimate["hourly_rate"]    = None
            print(c(C.YELLOW, "  Monthly estimate cleared."))
    except QuitToMenu:
        return

    input(c(C.CYAN, "\n  Preparing to disarm... Press Enter to continue"))

# ── Main menu ─────────────────────────────────────────────
def main():
    first_run = True
    while True:
        clear()
        if first_run:
            print()
            print(c(C.DIM, '  "We\'d like to share a limited-time inflight offer with you today..."'))
            print()
            first_run = False

        header("AMERICAN AIRLINES FA PAY CALCULATOR")
        mult, lbl = get_current_cba()
        print(c(C.GREEN, f"   2024 APFA CBA  |  Active rates: {lbl}\n"))
        # Show trip count if any in session
        n = len(monthly_estimate["trips"])
        trip_note = c(C.DIM, f"  ({n} trip{'s' if n != 1 else ''} in estimate)") if n > 0 else ""
        print("   1.  Calculate a new trip")
        print(f"   2.  Monthly pay estimate{trip_note}")
        print("   3.  View pay scale")
        print("   4.  View per diem rates")
        print("   5.  Contract glossary & pay reference")
        print(c(C.DIM, "   6.  Jump and slide\n"))

        choice = input("   Select → ").strip()

        if choice == "1":
            try:
                run_calculator()
                input(c(C.CYAN, "\n  Preparing to disarm... Press Enter to continue"))
            except QuitToMenu:
                pass
        elif choice == "2":
            view_monthly_estimate()
        elif choice == "3":
            view_pay_scale()
        elif choice == "4":
            view_per_diem()
        elif choice == "5":
            view_glossary()
        elif choice == "6":
            clear()
            print()
            print(c(C.YELLOW, "  Step out."))
            print(c(C.YELLOW, "  Follow the arrows."))
            print(c(C.YELLOW, "  Leave everything.\n"))
            print(c(C.GREEN,  "  This is O'Hare. This calculator is now out of service."))
            print(c(C.GREEN,  "  Please collect your per diem and exit."))
            print(c(C.GREEN,  "  Unattended bags will be given to a JAN."))
            print()
            sys.exit(0)
        else:
            print(c(C.RED, "  Leave everything! ...including that typo. Try 1–6."))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(c(C.YELLOW, "\n\n  Open seatbelts! Get out! Leave everything!\n"))
        sys.exit(0)
    except Exception as e:
        print(c(C.RED, f"\n  Error: {e}"))
        input("\n  Press Enter to close...")

# ============================================================
# HOW TO RUN
# ------------------------------------------------------------
# Windows PowerShell 7+:
#   cd C:\MyScripts
#   python fa_pay_calculator.py
#
# Mac Terminal:
#   cd /path/to/script
#   python3 fa_pay_calculator.py
#
# Requirements: Python 3.6+  |  No pip installs needed
# ============================================================
