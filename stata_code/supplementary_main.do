cd "/Users/zhaoxinhang/Desktop/disruptiveness-novelty/data" // Replace with the path to the folder on your computer
use "all-top5.dta", clear

asdoc summarize delay_year novelty author_count first_author_productivity team_productivity inter_coauthorship ///
    journal_tier Ni_dynamic Nj_dynamic citation_dynamic Ni_foreign_ratio Nj_foreign_ratio, save(Supplementary_Table10.doc) replace title(Table 10. Descriptive statistics and Spearman correlations)

asdoc pwcorr delay_year novelty author_count first_author_productivity team_productivity inter_coauthorship ///
    journal_tier Ni_dynamic Nj_dynamic citation_dynamic Ni_foreign_ratio Nj_foreign_ratio, spearman append


nbreg delay_year novelty author_count first_author_productivity team_productivity inter_coauthorship i.year if field==1, vce(robust)
outreg2 using Supplementary_Table2.doc, replace ctitle(Model 1) bdec(3) tdec(3) ///
addstat(Log-likelihood, e(ll), Wald chi2, e(chi2)) ///
addtext(Year FE, YES)

nbreg delay_year novelty author_count first_author_productivity team_productivity inter_coauthorship i.year if field==2, vce(robust)
outreg2 using Supplementary_Table2.doc, append ctitle(Model 2) bdec(3) tdec(3) ///
addstat(Log-likelihood, e(ll), Wald chi2, e(chi2)) ///
addtext(Year FE, YES)


nbreg delay_year novelty author_count first_author_productivity team_productivity inter_coauthorship i.year if field==3, vce(robust)
outreg2 using Supplementary_Table2.doc, append ctitle(Model 3) bdec(3) tdec(3) ///
addstat(Log-likelihood, e(ll), Wald chi2, e(chi2)) ///
addtext(Year FE, YES)

nbreg delay_year novelty author_count first_author_productivity team_productivity inter_coauthorship i.year if field==4, vce(robust)
outreg2 using Supplementary_Table2.doc, append ctitle(Model 4) bdec(3) tdec(3) ///
addstat(Log-likelihood, e(ll), Wald chi2, e(chi2)) ///
addtext(Year FE, YES)


nbreg delay_year c.novelty##i.journal_tier author_count first_author_productivity team_productivity inter_coauthorship i.year if field==1, vce(robust)
outreg2 using Supplementary_Table2.doc, append ctitle(Model 5) bdec(3) tdec(3) ///
addstat(Log-likelihood, e(ll), Wald chi2, e(chi2)) ///
addtext(Year FE, YES)


nbreg delay_year c.novelty##i.journal_tier author_count first_author_productivity team_productivity inter_coauthorship i.year if field==2, vce(robust)
outreg2 using Supplementary_Table2.doc, append ctitle(Model 6) bdec(3) tdec(3) ///
addstat(Log-likelihood, e(ll), Wald chi2, e(chi2)) ///
addtext(Year FE, YES)


nbreg delay_year c.novelty##i.journal_tier author_count first_author_productivity team_productivity  inter_coauthorship i.year if field==3, vce(robust)
outreg2 using Supplementary_Table2.doc, append ctitle(Model 7) bdec(3) tdec(3) ///
addstat(Log-likelihood, e(ll), Wald chi2, e(chi2)) ///
addtext(Year FE, YES)

