cd ".../Disruptiveness-novelty/data" // Replace with the path to the folder on your computer
use "all-top5.dta", clear

nbreg delay_year novelty team_size first_author_productivity team_productivity phrase_count inter_coauthorship i.year i.field, vce(robust)
outreg2 using Table1.doc, replace ctitle(Model 1) bdec(3) tdec(3) ///
addstat(Log-likelihood, e(ll), Wald chi2, e(chi2)) ///
addtext(Year FE, YES, Field FE, YES)


nbreg delay_year c.novelty##i.journal_tier team_size first_author_productivity team_productivity phrase_count inter_coauthorship i.year i.field, vce(robust)
outreg2 using Table1.doc, append ctitle(Model 2) bdec(3) tdec(3) ///
addstat(Log-likelihood, e(ll), Wald chi2, e(chi2)) ///
addtext(Year FE, YES, Field FE, YES)

gen Ni = log(1+Ni_dynamic)
reg Ni novelty team_size first_author_productivity team_productivity phrase_count inter_coauthorship delay_year journal_tier_orig5 i.year i.field, vce(robust)
outreg2 using Table2.doc, replace ctitle("Dependent variable: Ni") bdec(3) tdec(3) 

gen Nj = log(1+Nj_dynamic)
reg Nj novelty team_size first_author_productivity team_productivity phrase_count inter_coauthorship delay_year journal_tier_orig5 i.year i.field, vce(robust)
outreg2 using Table2.doc, append ctitle("Dependent variable: Nj") bdec(3) tdec(3)

gen citation = log(1+citation_dynamic)
reg citation novelty team_size first_author_productivity team_productivity phrase_count inter_coauthorship delay_year journal_tier_orig5 i.year i.field, vce(robust)
outreg2 using Table2.doc, append ctitle("Dependent variable: Citation") bdec(3) tdec(3) 

reg Ni_foreign_ratio novelty team_size first_author_productivity team_productivity phrase_count inter_coauthorship delay_year citation_dynamic journal_tier_orig5 i.year i.field, vce(robust)
outreg2 using Table2.doc, append ctitle("Dependent variable: Ni_foreign_ratio") bdec(3) tdec(3) 

reg Nj_foreign_ratio novelty team_size first_author_productivity team_productivity phrase_count inter_coauthorship delay_year citation_dynamic journal_tier_orig5 i.year i.field, vce(robust)
outreg2 using Table2.doc, append ctitle("Dependent variable: Nj_foreign_ratio") bdec(3) tdec(3) 








