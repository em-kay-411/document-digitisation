"""Generate a 10-page test PDF form: Small Business Loan Application.

Produces a realistic form with text fields, checkboxes, radio buttons,
dropdowns, date fields, and signature fields across 10 pages.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas
from reportlab.lib import colors

OUTPUT = "test_form.pdf"
W, H = letter  # 612 x 792

# Colors
BLUE = HexColor("#1a4b8c")
LIGHT_GRAY = HexColor("#f0f0f0")
MEDIUM_GRAY = HexColor("#999999")
DARK_GRAY = HexColor("#333333")


class FormBuilder:
    def __init__(self, filename):
        self.c = canvas.Canvas(filename, pagesize=letter)
        self.c.setTitle("Small Business Loan Application")
        self.page = 1
        self.y = H - 72  # start position
        self.field_count = 0

    def _field_name(self, name):
        self.field_count += 1
        return name

    def new_page(self):
        self.c.showPage()
        self.page += 1
        self.y = H - 72

    def ensure_space(self, needed):
        if self.y - needed < 72:
            self.new_page()

    # --- Drawing helpers ---

    def draw_header(self, title, subtitle=None):
        self.c.setFillColor(BLUE)
        self.c.rect(0, H - 50, W, 50, fill=1, stroke=0)
        self.c.setFillColor(white)
        self.c.setFont("Helvetica-Bold", 16)
        self.c.drawString(36, H - 35, "FIRST NATIONAL BANK")
        self.c.setFont("Helvetica", 9)
        self.c.drawRightString(W - 36, H - 25, f"Page {self.page} of 10")
        self.c.drawRightString(W - 36, H - 38, "Form SBL-2024 Rev. 03")
        self.y = H - 72

        self.c.setFillColor(DARK_GRAY)
        self.c.setFont("Helvetica-Bold", 14)
        self.c.drawString(36, self.y, title)
        self.y -= 16
        if subtitle:
            self.c.setFont("Helvetica", 9)
            self.c.setFillColor(MEDIUM_GRAY)
            self.c.drawString(36, self.y, subtitle)
            self.y -= 14
        self.c.setFillColor(black)
        self.y -= 8

    def section_title(self, title):
        self.ensure_space(30)
        self.c.setFillColor(BLUE)
        self.c.setFont("Helvetica-Bold", 11)
        self.c.drawString(36, self.y, title)
        self.c.setStrokeColor(BLUE)
        self.c.setLineWidth(0.5)
        self.c.line(36, self.y - 3, W - 36, self.y - 3)
        self.c.setFillColor(black)
        self.c.setStrokeColor(black)
        self.y -= 20

    def paragraph(self, text, font_size=9):
        self.c.setFont("Helvetica", font_size)
        self.c.setFillColor(DARK_GRAY)
        words = text.split()
        lines = []
        line = ""
        max_w = W - 72
        for word in words:
            test = f"{line} {word}".strip()
            if self.c.stringWidth(test, "Helvetica", font_size) < max_w:
                line = test
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)

        for l in lines:
            self.ensure_space(14)
            self.c.drawString(36, self.y, l)
            self.y -= 13
        self.c.setFillColor(black)
        self.y -= 4

    def label(self, text, x=36):
        self.c.setFont("Helvetica", 8)
        self.c.setFillColor(DARK_GRAY)
        self.c.drawString(x, self.y + 14, text)
        self.c.setFillColor(black)

    # --- Form field creators ---

    def text_field(self, name, label_text, x=36, width=240, height=18):
        self.ensure_space(34)
        self.label(label_text, x)
        field_name = self._field_name(name)
        self.c.acroForm.textfield(
            name=field_name,
            x=x, y=self.y - 4,
            width=width, height=height,
            borderWidth=1,
            borderColor=MEDIUM_GRAY,
            fillColor=LIGHT_GRAY,
            textColor=black,
            fontSize=9,
            fontName="Helvetica",
        )
        self.y -= 30

    def text_field_row(self, fields):
        """Draw multiple text fields on one row. fields: [(name, label, width), ...]"""
        self.ensure_space(34)
        x = 36
        gap = 12
        for name, lbl, width in fields:
            self.label(lbl, x)
            self.c.acroForm.textfield(
                name=self._field_name(name),
                x=x, y=self.y - 4,
                width=width, height=18,
                borderWidth=1,
                borderColor=MEDIUM_GRAY,
                fillColor=LIGHT_GRAY,
                textColor=black,
                fontSize=9,
                fontName="Helvetica",
            )
            x += width + gap
        self.y -= 30

    def multiline_field(self, name, label_text, x=36, width=540, height=60):
        self.ensure_space(height + 20)
        self.label(label_text, x)
        self.c.acroForm.textfield(
            name=self._field_name(name),
            x=x, y=self.y - height + 14,
            width=width, height=height,
            borderWidth=1,
            borderColor=MEDIUM_GRAY,
            fillColor=LIGHT_GRAY,
            textColor=black,
            fontSize=9,
            fontName="Helvetica",
            fieldFlags="multiline",
        )
        self.y -= height + 6

    def checkbox(self, name, label_text, x=36):
        self.ensure_space(18)
        self.c.acroForm.checkbox(
            name=self._field_name(name),
            x=x, y=self.y,
            size=12,
            borderWidth=1,
            borderColor=MEDIUM_GRAY,
            fillColor=white,
            buttonStyle="check",
        )
        self.c.setFont("Helvetica", 9)
        self.c.drawString(x + 18, self.y + 2, label_text)
        self.y -= 18

    def checkbox_row(self, items, x_start=36):
        """Draw checkboxes in a row. items: [(name, label), ...]"""
        self.ensure_space(18)
        x = x_start
        for name, lbl in items:
            self.c.acroForm.checkbox(
                name=self._field_name(name),
                x=x, y=self.y,
                size=12,
                borderWidth=1,
                borderColor=MEDIUM_GRAY,
                fillColor=white,
                buttonStyle="check",
            )
            self.c.setFont("Helvetica", 9)
            self.c.drawString(x + 16, self.y + 2, lbl)
            x += self.c.stringWidth(lbl, "Helvetica", 9) + 36
        self.y -= 18

    def radio_group(self, group_name, label_text, options):
        self.ensure_space(18 + len(options) * 18)
        self.c.setFont("Helvetica-Bold", 9)
        self.c.drawString(36, self.y, label_text)
        self.y -= 16
        for opt in options:
            self.c.acroForm.radio(
                name=self._field_name(group_name),
                value=opt.lower().replace(" ", "_"),
                x=50, y=self.y,
                size=12,
                borderWidth=1,
                borderColor=MEDIUM_GRAY,
                fillColor=white,
                buttonStyle="circle",
            )
            self.c.setFont("Helvetica", 9)
            self.c.drawString(68, self.y + 2, opt)
            self.y -= 17
        self.y -= 4

    def dropdown(self, name, label_text, options, x=36, width=240):
        self.ensure_space(34)
        self.label(label_text, x)
        self.c.acroForm.choice(
            name=self._field_name(name),
            value=options[0],
            options=options,
            x=x, y=self.y - 4,
            width=width, height=18,
            borderWidth=1,
            borderColor=MEDIUM_GRAY,
            fillColor=LIGHT_GRAY,
            textColor=black,
            fontSize=9,
            fontName="Helvetica",
            fieldFlags="combo",
        )
        self.y -= 30

    def date_field(self, name, label_text, x=36, width=140):
        self.ensure_space(34)
        self.label(label_text, x)
        self.c.acroForm.textfield(
            name=self._field_name(f"date_{name}"),
            x=x, y=self.y - 4,
            width=width, height=18,
            borderWidth=1,
            borderColor=MEDIUM_GRAY,
            fillColor=LIGHT_GRAY,
            textColor=black,
            fontSize=9,
            fontName="Helvetica",
            tooltip="MM/DD/YYYY",
        )
        self.c.setFont("Helvetica", 7)
        self.c.setFillColor(MEDIUM_GRAY)
        self.c.drawString(x + width + 4, self.y, "MM/DD/YYYY")
        self.c.setFillColor(black)
        self.y -= 30

    def signature_field(self, name, label_text, x=36, width=300, height=40):
        self.ensure_space(height + 24)
        self.label(label_text, x)
        # Draw signature box
        self.c.setStrokeColor(MEDIUM_GRAY)
        self.c.setDash(3, 3)
        self.c.rect(x, self.y - height + 14, width, height, fill=0, stroke=1)
        self.c.setDash()
        self.c.setFont("Helvetica", 7)
        self.c.setFillColor(MEDIUM_GRAY)
        self.c.drawString(x + 4, self.y - height + 18, "Sign here")
        self.c.setFillColor(black)
        self.c.setStrokeColor(black)
        # Overlay a text field for the signature
        self.c.acroForm.textfield(
            name=self._field_name(f"sig_{name}"),
            x=x, y=self.y - height + 14,
            width=width, height=height,
            borderWidth=0,
            fillColor=colors.Color(0, 0, 0, 0),
            textColor=black,
            fontSize=14,
            fontName="Helvetica-Oblique",
        )
        self.y -= height + 10

    def spacer(self, h=10):
        self.y -= h

    def build(self):
        self._page1()
        self._page2()
        self._page3()
        self._page4()
        self._page5()
        self._page6()
        self._page7()
        self._page8()
        self._page9()
        self._page10()
        self.c.save()
        print(f"Generated {OUTPUT} with {self.field_count} form fields across 10 pages")

    # ================================================================
    # PAGE 1 — Applicant Personal Information
    # ================================================================
    def _page1(self):
        self.draw_header(
            "SMALL BUSINESS LOAN APPLICATION",
            "Please complete all sections. Incomplete applications will not be processed."
        )

        self.paragraph(
            "Thank you for your interest in First National Bank's Small Business Lending Program. "
            "This application is used to evaluate your eligibility for loans up to $500,000 under our "
            "standard commercial lending guidelines. All information provided is subject to verification "
            "and will be handled in accordance with federal privacy regulations (GLBA). Please allow "
            "10-15 business days for processing after submission of a complete application."
        )

        self.section_title("Section 1: Primary Applicant Information")

        self.paragraph(
            "Provide the legal name of the primary applicant exactly as it appears on your government-issued "
            "identification. If applying as a business entity, also complete the business information section."
        )

        self.text_field_row([
            ("applicant_first_name", "First Name *", 160),
            ("applicant_middle_name", "Middle Name", 100),
            ("applicant_last_name", "Last Name *", 210),
        ])
        self.text_field_row([
            ("applicant_suffix", "Suffix", 60),
            ("applicant_ssn", "Social Security Number *", 160),
            ("applicant_dob", "Date of Birth (MM/DD/YYYY) *", 140),
        ])

        self.text_field("applicant_email", "Email Address *", width=300)
        self.text_field_row([
            ("applicant_phone_primary", "Primary Phone *", 180),
            ("applicant_phone_alt", "Alternate Phone", 180),
        ])

        self.dropdown("applicant_id_type", "Government ID Type *", [
            "-- Select --", "Driver's License", "Passport", "State ID",
            "Military ID", "Permanent Resident Card"
        ])
        self.text_field_row([
            ("applicant_id_number", "ID Number *", 200),
            ("applicant_id_state", "Issuing State", 100),
            ("applicant_id_expiry", "Expiration Date *", 140),
        ])

        self.section_title("Section 2: Current Residential Address")

        self.text_field("address_street1", "Street Address Line 1 *", width=540)
        self.text_field("address_street2", "Street Address Line 2", width=540)
        self.text_field_row([
            ("address_city", "City *", 200),
            ("address_state", "State *", 80),
            ("address_zip", "ZIP Code *", 100),
        ])

        self.dropdown("address_residence_type", "Residence Type", [
            "-- Select --", "Own", "Rent", "Live with family", "Other"
        ])
        self.text_field_row([
            ("address_years_at_address", "Years at Current Address", 100),
            ("address_monthly_payment", "Monthly Rent/Mortgage ($)", 140),
        ])

    # ================================================================
    # PAGE 2 — Co-Applicant & Employment
    # ================================================================
    def _page2(self):
        self.new_page()
        self.draw_header(
            "SMALL BUSINESS LOAN APPLICATION",
            "Section 3-4: Co-Applicant & Employment History"
        )

        self.section_title("Section 3: Co-Applicant Information (if applicable)")

        self.paragraph(
            "If there is a co-applicant (spouse, business partner, or guarantor), "
            "please provide their information below. A co-applicant's income and credit "
            "history will be considered in the evaluation. Co-applicants must also sign "
            "the authorization on Page 10."
        )

        self.checkbox("has_co_applicant", "Yes, there is a co-applicant for this loan")
        self.spacer(4)

        self.text_field_row([
            ("co_first_name", "Co-Applicant First Name", 170),
            ("co_middle_name", "Middle", 80),
            ("co_last_name", "Co-Applicant Last Name", 200),
        ])
        self.text_field_row([
            ("co_ssn", "SSN", 150),
            ("co_dob", "Date of Birth", 140),
            ("co_phone", "Phone Number", 160),
        ])
        self.text_field("co_email", "Email Address", width=300)

        self.dropdown("co_relationship", "Relationship to Primary Applicant", [
            "-- Select --", "Spouse", "Business Partner", "Family Member",
            "Guarantor", "Other"
        ])

        self.section_title("Section 4: Employment Information — Primary Applicant")

        self.paragraph(
            "List your current and previous employment for the past 5 years. Self-employment "
            "should be listed with your business name as employer. If retired, state 'Retired' "
            "and provide pension or retirement income details in the financial section."
        )

        self.c.setFont("Helvetica-Bold", 9)
        self.c.drawString(36, self.y, "Current Employment")
        self.y -= 16

        self.text_field("emp_current_employer", "Employer Name *", width=360)
        self.text_field_row([
            ("emp_current_title", "Job Title *", 200),
            ("emp_current_years", "Years Employed *", 100),
            ("emp_current_months", "Months", 60),
        ])
        self.text_field("emp_current_address", "Employer Address", width=400)
        self.text_field_row([
            ("emp_current_phone", "Employer Phone", 180),
            ("emp_current_salary", "Annual Salary/Income ($) *", 180),
        ])

        self.dropdown("emp_current_type", "Employment Type *", [
            "-- Select --", "Full-time", "Part-time", "Self-employed",
            "Contract", "Seasonal", "Retired"
        ])

        self.spacer(6)
        self.c.setFont("Helvetica-Bold", 9)
        self.c.drawString(36, self.y, "Previous Employment (if less than 2 years at current)")
        self.y -= 16

        self.text_field("emp_prev_employer", "Previous Employer Name", width=360)
        self.text_field_row([
            ("emp_prev_title", "Job Title", 200),
            ("emp_prev_years", "Years There", 100),
        ])

    # ================================================================
    # PAGE 3 — Business Information
    # ================================================================
    def _page3(self):
        self.new_page()
        self.draw_header(
            "SMALL BUSINESS LOAN APPLICATION",
            "Section 5: Business Information"
        )

        self.section_title("Section 5: Business Details")

        self.paragraph(
            "Provide complete information about the business for which you are seeking financing. "
            "If the business is not yet established, indicate 'Startup' for the business type and "
            "provide projected financial data where actual figures are requested. New businesses "
            "must also submit a comprehensive business plan (see Page 9 checklist)."
        )

        self.text_field("biz_legal_name", "Legal Business Name *", width=400)
        self.text_field("biz_dba", "DBA / Trade Name (if different)", width=400)
        self.text_field("biz_ein", "Federal EIN (Tax ID) *", width=200)

        self.dropdown("biz_entity_type", "Business Entity Type *", [
            "-- Select --", "Sole Proprietorship", "Partnership", "LLC",
            "S-Corporation", "C-Corporation", "Non-Profit", "Other"
        ])

        self.dropdown("biz_industry", "Industry / NAICS Code *", [
            "-- Select --", "Retail Trade", "Professional Services",
            "Construction", "Manufacturing", "Food & Accommodation",
            "Healthcare", "Technology", "Transportation", "Agriculture",
            "Real Estate", "Other"
        ])

        self.text_field_row([
            ("biz_established_date", "Date Established *", 140),
            ("biz_state_of_inc", "State of Incorporation", 120),
            ("biz_num_employees", "Number of Employees", 120),
        ])

        self.text_field("biz_address_street", "Business Street Address *", width=540)
        self.text_field_row([
            ("biz_address_city", "City *", 200),
            ("biz_address_state", "State *", 80),
            ("biz_address_zip", "ZIP Code *", 100),
        ])
        self.text_field_row([
            ("biz_phone", "Business Phone *", 180),
            ("biz_fax", "Fax", 140),
            ("biz_website", "Website", 180),
        ])

        self.section_title("Business Ownership")

        self.paragraph(
            "List all individuals or entities with 20% or more ownership. The total must equal 100%. "
            "Each owner with 20%+ ownership must complete a personal financial statement."
        )

        for i in range(1, 4):
            self.text_field_row([
                (f"owner{i}_name", f"Owner {i} Name", 200),
                (f"owner{i}_title", "Title", 120),
                (f"owner{i}_pct", "% Owned", 70),
                (f"owner{i}_ssn", "SSN", 120),
            ])

    # ================================================================
    # PAGE 4 — Loan Request Details
    # ================================================================
    def _page4(self):
        self.new_page()
        self.draw_header(
            "SMALL BUSINESS LOAN APPLICATION",
            "Section 6: Loan Request Details"
        )

        self.section_title("Section 6: Loan Request")

        self.paragraph(
            "Specify the loan amount, purpose, and terms you are requesting. Final terms are "
            "subject to credit approval and may differ from your request. Interest rates are "
            "determined based on creditworthiness, collateral, and prevailing market conditions. "
            "Current base rate: Prime + 1.5% (variable) or 7.25% (fixed, subject to change)."
        )

        self.text_field("loan_amount_requested", "Loan Amount Requested ($) *", width=200)

        self.radio_group("loan_purpose", "Purpose of Loan *", [
            "Working Capital / Operating Expenses",
            "Equipment Purchase",
            "Real Estate Purchase or Improvement",
            "Business Acquisition",
            "Debt Refinancing",
            "Startup Costs",
            "Inventory Purchase",
            "Other (specify below)"
        ])

        self.text_field("loan_purpose_other", "If Other, please specify:", width=400)

        self.radio_group("loan_term_pref", "Preferred Loan Term", [
            "Short-term (up to 1 year)",
            "Medium-term (1-5 years)",
            "Long-term (5-10 years)",
            "Line of Credit (revolving)"
        ])

        self.radio_group("loan_rate_pref", "Interest Rate Preference", [
            "Fixed Rate",
            "Variable Rate",
            "No Preference"
        ])

        self.date_field("loan_funds_needed_by", "Date Funds Needed By")

    # ================================================================
    # PAGE 5 — Financial Information
    # ================================================================
    def _page5(self):
        self.new_page()
        self.draw_header(
            "SMALL BUSINESS LOAN APPLICATION",
            "Section 7: Financial Information"
        )

        self.section_title("Section 7A: Personal Financial Summary")

        self.paragraph(
            "Provide your current personal financial information. All figures should be as of "
            "today's date. Jointly held assets should show the full value. This information will "
            "be verified against your credit report and tax returns."
        )

        self.c.setFont("Helvetica-Bold", 9)
        self.c.drawString(36, self.y, "Assets")
        self.y -= 16

        asset_fields = [
            ("asset_checking", "Checking Accounts ($)"),
            ("asset_savings", "Savings / Money Market ($)"),
            ("asset_investments", "Stocks / Bonds / Mutual Funds ($)"),
            ("asset_retirement", "Retirement Accounts (401k, IRA) ($)"),
            ("asset_real_estate", "Real Estate (market value) ($)"),
            ("asset_vehicles", "Vehicles (market value) ($)"),
            ("asset_other", "Other Assets ($)"),
            ("asset_total", "TOTAL ASSETS ($)"),
        ]
        for name, lbl in asset_fields:
            self.text_field_row([(name, lbl, 200)])

        self.spacer(4)
        self.c.setFont("Helvetica-Bold", 9)
        self.c.drawString(36, self.y, "Liabilities")
        self.y -= 16

        liability_fields = [
            ("liability_mortgage", "Mortgage Balance ($)"),
            ("liability_auto_loans", "Auto Loans ($)"),
            ("liability_credit_cards", "Credit Card Balances ($)"),
            ("liability_student_loans", "Student Loans ($)"),
            ("liability_other", "Other Liabilities ($)"),
            ("liability_total", "TOTAL LIABILITIES ($)"),
        ]
        for name, lbl in liability_fields:
            self.text_field_row([(name, lbl, 200)])

        self.text_field("net_worth", "NET WORTH (Assets - Liabilities) ($)", width=200)

    # ================================================================
    # PAGE 6 — Business Financials
    # ================================================================
    def _page6(self):
        self.new_page()
        self.draw_header(
            "SMALL BUSINESS LOAN APPLICATION",
            "Section 7B: Business Financial Summary"
        )

        self.section_title("Section 7B: Business Financial Summary")

        self.paragraph(
            "Provide key financial metrics for your business. If you are a startup, provide "
            "projected figures clearly marked as estimates. Attach your most recent balance sheet, "
            "income statement, and cash flow statement. If the business has been operating for "
            "more than one year, provide 2 years of financial statements and tax returns."
        )

        self.c.setFont("Helvetica-Bold", 9)
        self.c.drawString(36, self.y, "Revenue & Income (Most Recent Fiscal Year)")
        self.y -= 16

        self.text_field_row([
            ("biz_gross_revenue", "Gross Revenue ($) *", 200),
            ("biz_fiscal_year_end", "Fiscal Year End (MM/YYYY)", 160),
        ])
        self.text_field_row([
            ("biz_cost_of_goods", "Cost of Goods Sold ($)", 200),
            ("biz_gross_profit", "Gross Profit ($)", 200),
        ])
        self.text_field_row([
            ("biz_operating_expenses", "Total Operating Expenses ($)", 200),
            ("biz_net_income", "Net Income ($) *", 200),
        ])

        self.spacer(6)
        self.c.setFont("Helvetica-Bold", 9)
        self.c.drawString(36, self.y, "Prior Year (for comparison)")
        self.y -= 16

        self.text_field_row([
            ("biz_prev_gross_revenue", "Prior Year Gross Revenue ($)", 200),
            ("biz_prev_net_income", "Prior Year Net Income ($)", 200),
        ])

        self.section_title("Business Banking Information")

        self.text_field("biz_bank_name", "Primary Business Bank *", width=300)
        self.text_field_row([
            ("biz_bank_account", "Account Number", 200),
            ("biz_bank_avg_balance", "Average Monthly Balance ($)", 200),
        ])

        self.checkbox("biz_existing_customer", "I am an existing First National Bank customer")
        self.text_field("biz_existing_account", "If yes, account number:", width=200)

        self.section_title("Outstanding Business Debts")

        self.paragraph(
            "List all existing business loans, lines of credit, and other obligations:"
        )

        for i in range(1, 4):
            self.text_field_row([
                (f"debt{i}_creditor", f"Creditor {i}", 160),
                (f"debt{i}_balance", "Balance ($)", 120),
                (f"debt{i}_payment", "Monthly Pmt ($)", 120),
                (f"debt{i}_rate", "Rate %", 60),
            ])

    # ================================================================
    # PAGE 7 — Collateral
    # ================================================================
    def _page7(self):
        self.new_page()
        self.draw_header(
            "SMALL BUSINESS LOAN APPLICATION",
            "Section 8: Collateral & Security"
        )

        self.section_title("Section 8: Collateral Offered")

        self.paragraph(
            "Most small business loans require collateral to secure the obligation. Collateral "
            "may include real estate, equipment, inventory, accounts receivable, or other business "
            "or personal assets. The bank reserves the right to require additional collateral or "
            "a personal guarantee. Collateral will be appraised by a bank-approved appraiser at "
            "the applicant's expense."
        )

        self.radio_group("collateral_type", "Primary Collateral Type *", [
            "Commercial Real Estate",
            "Residential Real Estate",
            "Equipment / Machinery",
            "Inventory",
            "Accounts Receivable",
            "Vehicles / Fleet",
            "Cash Savings / CD",
            "None / Unsecured Request"
        ])

        self.text_field("collateral_description", "Description of Collateral *", width=540)
        self.text_field_row([
            ("collateral_est_value", "Estimated Value ($) *", 200),
            ("collateral_current_liens", "Existing Liens ($)", 200),
        ])
        self.text_field("collateral_location", "Location of Collateral (if physical asset)", width=540)

        self.spacer(6)
        self.c.setFont("Helvetica-Bold", 9)
        self.c.drawString(36, self.y, "Additional Collateral (if any)")
        self.y -= 16

        self.text_field("collateral2_description", "Description", width=540)
        self.text_field_row([
            ("collateral2_est_value", "Estimated Value ($)", 200),
            ("collateral2_liens", "Existing Liens ($)", 200),
        ])

        self.section_title("Personal Guarantee")

        self.paragraph(
            "A personal guarantee may be required from all owners with 20% or more ownership "
            "in the business. By checking below, you acknowledge willingness to provide a "
            "personal guarantee."
        )

        self.checkbox("guarantee_primary", "Primary applicant agrees to provide personal guarantee")
        self.checkbox("guarantee_co", "Co-applicant agrees to provide personal guarantee")
        self.checkbox("guarantee_other", "Other guarantor (attach separate guarantee form)")

    # ================================================================
    # PAGE 8 — Declarations & Disclosures
    # ================================================================
    def _page8(self):
        self.new_page()
        self.draw_header(
            "SMALL BUSINESS LOAN APPLICATION",
            "Section 9: Declarations"
        )

        self.section_title("Section 9: Applicant Declarations")

        self.paragraph(
            "Answer the following questions for BOTH the primary applicant and co-applicant "
            "(if applicable). If you answer 'Yes' to any question, provide a written explanation "
            "on a separate sheet and attach it to this application. False statements may result "
            "in denial of the application and may constitute a federal crime."
        )

        declarations = [
            ("decl_bankruptcy", "Have you declared bankruptcy in the past 7 years?"),
            ("decl_foreclosure", "Have you had property foreclosed upon in the past 7 years?"),
            ("decl_lawsuit", "Are you currently party to any lawsuit or legal action?"),
            ("decl_tax_lien", "Are there any outstanding tax liens against you or your business?"),
            ("decl_delinquent", "Are you currently delinquent on any federal debt (taxes, student loans, etc.)?"),
            ("decl_felony", "Have you been convicted of a felony in the past 10 years?"),
            ("decl_obligation", "Are you obligated to pay alimony, child support, or separate maintenance?"),
            ("decl_other_apps", "Have you applied for other loans in the past 90 days?"),
            ("decl_government", "Are you or your business a government entity or official?"),
            ("decl_related_party", "Do you have any relationship with a First National Bank employee or director?"),
        ]

        for name, question in declarations:
            self.ensure_space(24)
            self.c.setFont("Helvetica", 9)
            self.c.drawString(36, self.y + 2, question)
            # Yes/No checkboxes
            self.c.acroForm.checkbox(
                name=self._field_name(f"{name}_yes"),
                x=460, y=self.y,
                size=12,
                borderWidth=1,
                borderColor=MEDIUM_GRAY,
                fillColor=white,
                buttonStyle="check",
            )
            self.c.drawString(476, self.y + 2, "Yes")
            self.c.acroForm.checkbox(
                name=self._field_name(f"{name}_no"),
                x=510, y=self.y,
                size=12,
                borderWidth=1,
                borderColor=MEDIUM_GRAY,
                fillColor=white,
                buttonStyle="check",
            )
            self.c.drawString(526, self.y + 2, "No")
            self.y -= 22

        self.spacer(6)
        self.multiline_field(
            "decl_explanation",
            "If you answered 'Yes' to any of the above, please explain:",
            height=80,
        )

    # ================================================================
    # PAGE 9 — Document Checklist & Additional Info
    # ================================================================
    def _page9(self):
        self.new_page()
        self.draw_header(
            "SMALL BUSINESS LOAN APPLICATION",
            "Section 10: Document Checklist & Additional Information"
        )

        self.section_title("Section 10A: Required Documents Checklist")

        self.paragraph(
            "Please check each document you are submitting with this application. All checked "
            "items must be included for the application to be considered complete. Missing documents "
            "will delay processing. Copies are acceptable unless otherwise noted."
        )

        docs = [
            ("doc_tax_personal_1", "Personal tax returns — most recent year"),
            ("doc_tax_personal_2", "Personal tax returns — prior year"),
            ("doc_tax_business_1", "Business tax returns — most recent year"),
            ("doc_tax_business_2", "Business tax returns — prior year"),
            ("doc_financial_stmt", "Business financial statements (balance sheet & income statement)"),
            ("doc_bank_statements", "Business bank statements — last 6 months"),
            ("doc_personal_bank", "Personal bank statements — last 3 months"),
            ("doc_business_plan", "Business plan (required for startups)"),
            ("doc_articles", "Articles of Incorporation / Organization"),
            ("doc_licenses", "Business licenses and permits"),
            ("doc_lease", "Commercial lease agreement (if applicable)"),
            ("doc_id_copy", "Copy of government-issued photo ID"),
            ("doc_insurance", "Proof of business insurance"),
            ("doc_ap_ar", "Accounts receivable / payable aging report"),
            ("doc_collateral_docs", "Collateral documentation (titles, deeds, appraisals)"),
        ]

        for name, lbl in docs:
            self.checkbox(name, lbl)

        self.spacer(8)
        self.section_title("Section 10B: Additional Information")

        self.paragraph(
            "Use the space below to provide any additional information that may help us "
            "evaluate your application, including business achievements, contracts in hand, "
            "growth projections, or any circumstances you would like to explain."
        )

        self.multiline_field("additional_info", "Additional Information:", height=100)

        self.dropdown("hear_about_us", "How did you hear about our lending program?", [
            "-- Select --", "Existing customer", "Referral", "Website",
            "Advertisement", "Business association", "CPA / Attorney", "Other"
        ])

        self.text_field("referral_name", "If referred, by whom?", width=300)

    # ================================================================
    # PAGE 10 — Authorization, Signatures, Dates
    # ================================================================
    def _page10(self):
        self.new_page()
        self.draw_header(
            "SMALL BUSINESS LOAN APPLICATION",
            "Section 11: Authorization & Signatures"
        )

        self.section_title("Section 11: Certification & Authorization")

        self.paragraph(
            "By signing below, I/we certify that all information provided in this application "
            "is true, complete, and correct to the best of my/our knowledge. I/we understand "
            "that any intentional misrepresentation of information may result in civil liability "
            "and/or criminal penalties including fine and imprisonment under applicable federal "
            "and state laws (18 U.S.C. § 1014)."
        )

        self.paragraph(
            "I/we authorize First National Bank and its agents to: (1) verify all information "
            "provided in this application through any means including credit bureaus, employers, "
            "and financial institutions; (2) obtain consumer credit reports in connection with "
            "this application and any update, renewal, or extension of credit; (3) share "
            "information about this application and account with affiliates and credit bureaus "
            "as permitted by law."
        )

        self.paragraph(
            "I/we further acknowledge that: (a) the bank is not obligated to approve this "
            "application; (b) approval is contingent upon satisfactory completion of the bank's "
            "underwriting process; (c) terms and conditions of any approved loan will be set "
            "forth in a separate loan agreement; (d) fees and costs associated with processing "
            "this application may apply and are described in the bank's fee schedule."
        )

        self.spacer(6)
        self.checkbox("agree_terms", "I/We have read and agree to the terms and conditions above *")
        self.checkbox("agree_credit_check", "I/We authorize credit report inquiries *")
        self.checkbox("agree_electronic", "I/We consent to electronic communications regarding this application")

        self.spacer(10)
        self.section_title("Primary Applicant Signature")

        self.text_field("print_name_primary", "Printed Name *", width=300)
        self.signature_field("primary_applicant", "Signature *")
        self.date_field("signed_primary", "Date Signed *")

        self.spacer(10)
        self.section_title("Co-Applicant / Guarantor Signature")

        self.text_field("print_name_co", "Printed Name", width=300)
        self.signature_field("co_applicant", "Signature")
        self.date_field("signed_co", "Date Signed")

        self.spacer(10)
        self.section_title("For Bank Use Only")

        self.paragraph(
            "This section is to be completed by the loan officer. Do not write below this line."
        )

        self.text_field_row([
            ("bank_officer_name", "Loan Officer Name", 200),
            ("bank_officer_id", "Officer ID", 100),
            ("bank_branch", "Branch", 160),
        ])
        self.date_field("bank_received_date", "Date Received")
        self.text_field("bank_application_id", "Application Number", width=200)
        self.dropdown("bank_status", "Initial Status", [
            "-- Select --", "Received", "Under Review", "Additional Info Needed",
            "Approved", "Conditionally Approved", "Denied", "Withdrawn"
        ])
        self.multiline_field("bank_notes", "Officer Notes:", height=50)


if __name__ == "__main__":
    fb = FormBuilder(OUTPUT)
    fb.build()
