# Project Plan: Application Data Analysis (Home Credit)

## Objective
To analyze the primary `application` dataset containing demographic, financial, and behavioral information about loan applicants. This analysis identifies key risk factors associated with default (`target`) and guides feature engineering for the Gold Layer.

## Approach
Columns are grouped into logical categories based on business meaning. For each group, hypotheses are formulated and tested using SQL aggregations. The final output includes feature engineering recommendations.

---

## Group 1: Data Quality and Primary Key Validation

**Columns involved:** `loanId` (`SK_ID_CURR`), `target`  
**Hypothesis:**  
- Primary key `loanId` must be unique and non‑null to ensure data integrity.

**What to analyze:**  
- Total row count, null count, and duplicate count for `loanId`.

### Results

| total_rows | null_count | duplicate_count |
|------------|------------|-----------------|
| 307,511    | 0          | 0               |

**Insight:** The data is clean; no missing or duplicate `loanId`s. This validates data integrity.

---

## Group 2: Contract Type and Loan Characteristics

**Columns involved:** `contractType` (`NAME_CONTRACT_TYPE`), `creditAmt`, `annuityAmt`, `incomeTotal`  
**Hypothesis:**  
- `Cash loans` and `Revolving loans` have different risk profiles.  
- High debt‑to‑income ratio (`creditAmt / incomeTotal`) is a strong predictor of default.

**What to analyze:**  
- Default rate per contract type.  
- Average credit amount, annuity, income, and debt‑to‑income ratio per contract type.

### Results

**Default Rate by Contract Type**

| contractType | total_customer | default_rate |
|--------------|----------------|--------------|
| Cash loans   | 278,232        | 8.35%        |
| Revolving loans | 29,279      | 5.48%        |

**Financial Averages by Contract Type**

| contractType | avg_credit | avg_annuity | avg_income | avg_debt_to_income |
|--------------|------------|-------------|------------|---------------------|
| Revolving loans | 324,018 | 16,317 | 166,217 | 2.15 |
| Cash loans   | 627,966 | 28,244 | 169,070 | **4.15** |

**Insight:**  
- Cash loans have a significantly higher default rate (8.35% vs 5.48%).  
- Despite similar average income, Cash loans have nearly double the debt‑to‑income ratio (4.15 vs 2.15), indicating higher financial burden.

**Feature Recommendation:**  
- Use `debt_to_income = creditAmt / incomeTotal` as a numeric feature.  
- Use `contractType` as a binary or categorical feature (e.g., `is_cash_loan`).

---

## Group 3: Demographic and Socioeconomic Indicators

### Subgroup 3.1: Suite Type (Who Accompanies the Applicant)

**Columns involved:** `suiteType` (`NAME_TYPE_SUITE`)  
**Hypothesis:**  
- Applicants accompanied by family or spouse are more stable and lower risk.  
- Those applying alone (`Unaccompanied`) may have higher default rates.

**Results:**

| suiteType | total_customer | default_rate |
|-----------|----------------|--------------|
| Other_B | 1,770 | 9.83% |
| Other_A | 866 | 8.78% |
| Group of people | 271 | 8.49% |
| Unaccompanied | 248,526 | 8.18% |
| Spouse, partner | 11,370 | 7.87% |
| Family | 40,149 | 7.49% |
| Children | 3,267 | 7.38% |
| None | 1,292 | 5.42% |

**Insight:**  
- `Unaccompanied` dominates but has default rate close to average.  
- `None` and `Children` have lower risk; `Other_B` and `Other_A` show higher risk but small samples.  
- Grouping rare categories into `Others` is recommended.

**Feature Recommendation:**  
- Create binary flags:  
  - `is_accompanied = 1` if suiteType is not `Unaccompanied` or `None` (or domain‑specific).  
  - Or group into `low_risk`, `medium_risk`, `high_risk` based on default rates.

---

### Subgroup 3.2: Own Car and Own Realty

**Columns involved:** `ownCar`, `ownRealty`  
**Hypothesis:**  
- Owning assets (car and/or house) lowers default risk.

**Results:**

| ownCar | ownRealty | total_customer | default_rate |
|--------|-----------|----------------|--------------|
| N | N | 61,972 | 8.99% |
| N | Y | 140,952 | 8.28% |
| Y | Y | 72,360 | 7.33% |
| Y | N | 32,227 | **7.04%** |

**Financial Averages by Asset Ownership:**

| ownCar | ownRealty | avg_income | avg_annuity | avg_credit | avg_payment_ratio (annuity/income) |
|--------|-----------|------------|-------------|------------|-----------------------------------|
| Y | N | 197,131 | 29,898 | 693,807 | 0.172 |
| Y | Y | 195,986 | 29,998 | 650,994 | 0.173 |
| N | Y | 155,540 | 25,549 | 556,452 | 0.183 |
| N | N | 152,473 | 25,831 | 585,891 | 0.190 |

**Insight:**  
- The `Y,N` group (own car, rent) has the lowest default rate (7.04%), highest income, and lowest payment ratio.  
- The `N,N` group (neither) has the highest default rate (8.99%) and highest payment ratio.

**Feature Recommendation:**  
- Create a 4‑level categorical feature: `asset_profile` = `Both`, `Only Car`, `Only House`, `None`.  
- Or use binary flags `has_car`, `has_house`.

---

### Subgroup 3.3: Income Type

**Columns involved:** `incomeType`, `incomeTotal`, `creditAmt`  
**Hypothesis:**  
- Stable income types (`State servant`, `Pensioner`) have lower default rates.  
- High debt‑to‑income ratio correlates with higher default risk.

**Results:**

| incomeType | total | default_rate | avg_income | avg_credit | avg_ratio (credit/income) |
|------------|-------|--------------|------------|------------|---------------------------|
| Maternity leave | 5 | 40.0% | 140,400 | 749,700 | 8.29 |
| Unemployed | 22 | 36.4% | 110,536 | 764,386 | 11.87 |
| Working | 158,774 | 9.6% | 163,170 | 577,011 | 3.89 |
| Commercial associate | 71,617 | 7.5% | 202,955 | 669,913 | 3.69 |
| State servant | 21,703 | 5.8% | 179,738 | 669,819 | 4.17 |
| Pensioner | 55,362 | 5.4% | 136,401 | 542,546 | 4.41 |
| Student | 18 | 0.0% | 170,500 | 510,788 | 3.59 |
| Businessman | 10 | 0.0% | 652,500 | 1,228,500 | 2.86 |

**Insight:**  
- `Unemployed` and `Maternity leave` have extremely high default rates but tiny sample sizes – treat as noise.  
- `State servant` and `Pensioner` have low default rates despite moderate ratios, indicating stability.  
- `Working` and `Commercial associate` are the majority and have moderate risk.

**Feature Recommendation:**  
- Group income types into 3 categories:  
  - `Stable` = State servant, Pensioner  
  - `Private` = Working, Commercial associate  
  - `Others/Rare` = Maternity leave, Unemployed, Student, Businessman  
- Use as a categorical feature.

---

### Subgroup 3.4: Occupation

**Columns involved:** `occupation`, `incomeTotal`, `creditAmt`, `famMembers`  
**Hypothesis:**  
- Specific occupations have inherent risk profiles; manual labor and low‑skill jobs are riskier.

**Results (excerpt):**

| occupation | total | default_rate | avg_income | avg_credit | avg_ratio |
|------------|-------|--------------|------------|------------|-----------|
| Low-skill Laborers | 2,093 | 17.2% | 133,228 | 458,465 | 3.66 |
| Drivers | 18,603 | 11.3% | 187,012 | 612,334 | 3.51 |
| Laborers | 55,186 | 10.6% | 166,357 | 570,618 | 3.75 |
| Managers | 21,371 | 6.2% | 260,337 | 775,091 | 3.47 |
| Accountants | 9,813 | 4.8% | 194,578 | 709,757 | 4.01 |

**Insight:**  
- Low‑skill occupations (Laborers, Drivers, Security) show higher default rates.  
- Professional roles (Managers, Accountants, IT) have lower risk.  
- The `None` category (96,391 customers) has moderate default rate (6.5%) – may represent missing or unknown.

**Feature Recommendation:**  
- Group occupations into three risk levels:  
  - `High Risk` = Low‑skill Laborers, Drivers, Waiters/barmen, Security, Laborers, Cooking, Cleaning  
  - `Medium Risk` = Sales, Realty, Secretaries, Private service, Core staff, None  
  - `Low Risk` = Managers, Accountants, IT, HR, Medicine, High skill tech  
- Use `occupation_risk_group` as a categorical feature.

---

## Group 4: Financial Ratios and Outliers

### Subgroup 4.1: Annuity Distribution by Home Ownership

**Columns involved:** `ownRealty`, `annuityAmt`  
**Hypothesis:**  
- Homeowners might have higher annuity (due to larger loans or KPR), but data shows otherwise.

**Results:**

| ownRealty | totalCust | minAnnuity | maxAnnuity | avgAnnuity | median_annuity | countGt100k | pctGt100k |
|-----------|-----------|------------|------------|------------|----------------|-------------|-----------|
| N (rent)  | 94,199    | 2,052      | 258,026    | 27,223     | 24,903         | 158         | 0.17%     |
| Y (own)   | 213,312   | 1,616      | 225,000    | 27,058     | 24,903         | 347         | 0.16%     |

**Insight:**  
- Annuity amounts are nearly identical between renters and homeowners.  
- Very few customers have annuity > 100k (<0.2%).  
- Hypothesis not supported; `annuityAmt` is already available as a numeric feature.

**Feature Recommendation:**  
- No new feature needed; `annuityAmt` can be used as is.

---

### Subgroup 4.2: Goods Price and Credit Amount Difference

**Columns involved:** `creditAmt`, `goodsPrice`  
**Hypothesis:**  
- Large positive difference (`creditAmt > goodsPrice`) may indicate extra fees or errors, correlating with higher risk.  
- Negative difference indicates down payment, lowering risk.

**Results (excerpt):**

| case_type | diff | avg_target |
|-----------|------|------------|
| Positif (Pinjaman > Harga) | +540k | 0.0 |
| Negatif (Uang Muka) | -765k | 0.0 |

**Insight:**  
- Extreme differences (top 10 positive and negative) all had `target=0` – not representative.  
- Most loans have `creditAmt` close to `goodsPrice`; extreme differences are rare.  
- Only 278 records have `goodsPrice = 0` or `NULL`; the rest have non‑zero `goodsPrice`.

**Feature Recommendation:**  
- Create a binary flag `has_down_payment = 1 if creditAmt < goodsPrice else 0`.  
- Create a flag `has_extra_fees = 1 if creditAmt > goodsPrice * 1.2` (to catch large positive differences).  
- Avoid using raw `goodsPrice` due to missing values; focus on the difference.

---

## Group 5: Stability Indicators

### Subgroup 5.1: Registration and Identity Stability (`daysReg`, `daysIdPub`)

**Columns involved:** `daysReg`, `daysIdPub`  
**Hypothesis:**  
- Frequent changes (days close to 0) indicate instability and higher risk.  
- Long‑term stability lowers risk.

**Results:**

| reg_duration | id_duration | total | default_rate |
|--------------|-------------|-------|--------------|
| Reg: < 1 year | ID: < 1 year | 1,408 | 12.64% |
| Reg: < 1 year | ID: 1-3 years | 2,037 | 12.37% |
| ... | ... | ... | ... |
| Reg: > 10 years | ID: > 10 years | 84,920 | 6.38% |

**Insight:**  
- Strong correlation: recent changes in both registration and ID yield the highest default rates.  
- Both stable (>10 years) have the lowest default rate (6.38%).

**Feature Recommendation:**  
- Create a `stability_score`:  
  - `2` if both `daysReg` and `daysIdPub` are older than 3,650 days (>10 years)  
  - `1` if either is older than 3,650 days  
  - `0` otherwise  
- Or use binary flags: `is_recent_change = 1` if either `daysReg` or `daysIdPub` is > -365.

---

### Subgroup 5.2: Commuter Profile (`liveNotWork`, `liveCityNotWork`)

**Columns involved:** `liveNotWork`, `liveCityNotWork`  
**Hypothesis:**  
- Commuters (different work and home locations) may have higher default rates.  
- Local commuters (same region, different city) might have the highest risk.

**Results:**

| liveNotWork | liveCityNotWork | total | default_rate |
|-------------|-----------------|-------|--------------|
| 0 | 1 | 47,454 | 10.03% |
| 1 | 1 | 7,761 | 9.56% |
| 0 | 0 | 247,554 | 7.68% |
| 1 | 0 | 4,742 | 6.62% |

**Insight:**  
- `liveNotWork=0, liveCityNotWork=1` (different city but same region – local commuter) has the **highest** default rate (10.03%).  
- Fully stable (`0,0`) has the lowest risk among large groups.  
- The `1,0` combination (different region but same city) is likely data anomaly and should be ignored.

**Feature Recommendation:**  
- Create a categorical feature `commute_risk_profile`:  
  - `Stabil` = 0,0  
  - `Komuter Lokal` = 0,1  
  - `Komuter Jauh` = 1,1  
  - `Lainnya` = 1,0  
- Use as a 4‑level categorical feature.

---

### Subgroup 5.3: Region Rating (`regionRate`)

**Columns involved:** `regionRate`  
**Hypothesis:**  
- Higher region rating (3) indicates riskier areas, leading to higher default rates.

**Results:**

| regionRate | avg_income | avg_credit | avg_ratio | default_rate |
|------------|------------|------------|-----------|--------------|
| 1 | 242,402 | 759,991 | 3.52 | 4.82% |
| 2 | 161,893 | 581,611 | 3.97 | 7.89% |
| 3 | 152,195 | 573,583 | 4.20 | 11.10% |

**Insight:**  
- Clear monotonic increase: higher `regionRate` → higher default rate.  
- Region 3 has the highest debt‑to‑income ratio (4.20) and default rate (11.1%).  
- This is a strong independent predictor.

**Feature Recommendation:**  
- Use `regionRate` as a numeric feature (1,2,3).  
- Alternatively, create binary flags `is_region_3` or treat as categorical.

---

## Group 6: Behavioral and Contact Features

### Subgroup 6.1: Contact Score (`flagMobil`, `empPhone`, etc.)

**Columns involved:** `flagMobil`, `empPhone`, `workPhone`, `contMobile`, `flagPhone`, `flagEmail`  
**Hypothesis:**  
- More contact points indicate reliability and lower risk.

**Results:**

| contact_score | total | default_rate |
|---------------|-------|--------------|
| 6 | 1,992 | 8.99% |
| 5 | 35,492 | 8.39% |
| 4 | 70,671 | 8.50% |
| 3 | 160,972 | 8.38% |
| 2 | 38,357 | **5.67%** |
| 1 | 27 | 3.70% |

**Insight:**  
- `contact_score` does not show a clear monotonic relationship.  
- Lower scores (2) actually have lower default rates, likely because many are pensioners or stable workers who don't provide many contacts.  
- This feature is confounded by income type and age.

**Feature Recommendation:**  
- **Do not use** `contact_score` as a standalone feature.  
- If needed, create a binary flag `is_contact_complete = 1 if contact_score >= 3 else 0`, but expect limited predictive power.

---

### Subgroup 6.2: Application Time (`weekdayApp`, `hourApp`)

**Columns involved:** `weekdayApp`, `hourApp`  
**Hypothesis:**  
- Weekend or late‑night applications may be impulsive and riskier.

**Results (weekday):**

| weekdayApp | total | default_rate |
|------------|-------|--------------|
| TUESDAY | 53,901 | 8.35% |
| ... | ... | ... |
| MONDAY | 50,714 | 7.76% |

Differences are very small; weekday is **not** a strong predictor.

**Results (hour buckets):**

| app_time_group | total | default_rate |
|----------------|-------|--------------|
| Dini Hari (0-5) | 7,389 | 9.58% |
| Pagi (6-11) | 132,435 | 8.47% |
| Siang (12-17) | 152,998 | 7.76% |
| Malam (18-23) | 14,689 | 6.99% |

**Insight:**  
- Dini Hari (early morning) has significantly higher default rate.  
- Malam (evening) has the lowest – possibly more planned.

**Feature Recommendation:**  
- Use `is_dini_hari = 1 if hourApp between 0 and 5 else 0`.  
- Ignore `weekdayApp`.

---

## Group 7: Other Features

Several other features like `EXT_SOURCE_1/2/3`, `ORGANIZATION_TYPE`, and building property columns were analyzed. Recommendations:

- Use `EXT_SOURCE_1`, `EXT_SOURCE_2`, `EXT_SOURCE_3` as numeric features (they are strong predictors).  
- Use `ageYears` and `yearsEmployed` as numeric.  
- Use `childrenCnt` and `famMembers` as numeric; optionally combine into `income_per_member`.  
- Use `org_risk_group` (Stable/Risky/Others) for organization type.  
- Building property features (AVG/MODE/MEDI) are highly correlated; select only a few representative ones, e.g., `avgYrsBuild`, `avgApt`, `modeEmerg`.

---

## 🛠️ Final Feature Engineering Recommendations for Gold Layer

Based on the application analysis, the following features are recommended for inclusion in the Gold Layer:

| Feature Name | Type | Description |
|--------------|------|-------------|
| `loanId` | ID | Unique customer identifier |
| `target` | Label | Default indicator (0/1) |
| `ageYears` | Numeric | Age in years (integer) |
| `gender` | Categorical | Gender (binary) |
| `contractType` | Categorical | Cash loans / Revolving loans |
| `debt_to_income` | Numeric | `creditAmt / incomeTotal` |
| `payment_to_income` | Numeric | `annuityAmt / incomeTotal` |
| `incomeType_group` | Categorical | `Stable`, `Private`, `Others/Rare` |
| `occupation_risk_group` | Categorical | `High`, `Medium`, `Low` risk |
| `org_risk_group` | Categorical | `Stable`, `Risky`, `Others` |
| `has_car` | Binary | `ownCar = 1` |
| `has_house` | Binary | `ownRealty = 1` |
| `asset_profile` | Categorical | `Both`, `Only Car`, `Only House`, `None` |
| `has_down_payment` | Binary | `creditAmt < goodsPrice` |
| `is_high_utilization` | Binary | `debt_to_income > 4` (or custom threshold) |
| `stability_score` | Categorical | 0,1,2 based on `daysReg` and `daysIdPub` |
| `commute_risk_profile` | Categorical | `Stabil`, `Komuter Lokal`, `Komuter Jauh`, `Lainnya` |
| `regionRate` | Numeric | 1,2,3 |
| `is_dini_hari` | Binary | `hourApp between 0 and 5` |
| `EXT_SOURCE_1`, `EXT_SOURCE_2`, `EXT_SOURCE_3` | Numeric | External credit scores |
| `daysPhone` | Numeric | Days since last phone change |
| `childrenCnt`, `famMembers` | Numeric | Family size |
| `income_per_member` | Numeric | `incomeTotal / famMembers` |

**Features to exclude:**
- `weekdayApp` – weak signal.  
- `contact_score` – confounded.  
- Most `FLAG_DOCUMENT_*` – minimal impact (except possibly `doc2`, `doc3`, `doc4`).  
- Most building property columns – use only a few representative ones.

---

## Next Steps

1.  **Aggregate** features from the application table and join with aggregated features from `bureau`, `previous_application`, `POS_CASH`, `installments`, and `credit_card` to create a single Gold Layer table.
2.  **Validate** selected features on the test set.
3.  **Implement** the feature engineering pipeline in the Silver DAG and produce the final Gold Layer for model training.

The application analysis is complete and ready for integration into the overall feature engineering pipeline.