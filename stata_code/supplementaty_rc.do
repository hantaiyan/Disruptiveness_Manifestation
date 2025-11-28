cd ".../Disruptiveness-novelty/data" // Replace with the path to the folder on your computer
use "all-top5.dta", clear

gen novelty_n_p = log(1+new_phrase)
nbreg delay_year novelty_n_p team_size first_author_productivity team_productivity phrase_count inter_coauthorship i.year i.field, vce(robust)
outreg2 using Supplementary_Table3.doc, replace ctitle(Model 1) bdec(3) tdec(3) ///
addstat(Log-likelihood, e(ll), Wald chi2, e(chi2)) ///
addtext(Year FE, YES, Field FE, YES)

gen novelty_n_w_c = log(1+new_phrase)
nbreg delay_year novelty_n_w_c team_size first_author_productivity team_productivity phrase_count inter_coauthorship i.year i.field, vce(robust)
outreg2 using Supplementary_Table3.doc, append ctitle(Model 2) bdec(3) tdec(3) ///
addstat(Log-likelihood, e(ll), Wald chi2, e(chi2)) ///
addtext(Year FE, YES, Field FE, YES)


nbreg delay_year c.novelty##i.journal_tier_rc team_size first_author_productivity team_productivity phrase_count inter_coauthorship i.year i.field, vce(robust)
outreg2 using Supplementary_Table3.doc, append ctitle(Model 3) bdec(3) tdec(3) ///
addstat(Log-likelihood, e(ll), Wald chi2, e(chi2)) ///
addtext(Year FE, YES, Field FE, YES)


use "all-top3.dta", clear 
nbreg delay_year novelty team_size first_author_productivity team_productivity phrase_count inter_coauthorship i.year i.field, vce(robust)
outreg2 using Supplementary_Table3.doc, append ctitle(Model 4) bdec(3) tdec(3) ///
addstat(Log-likelihood, e(ll), Wald chi2, e(chi2)) ///
addtext(Year FE, YES, Field FE, YES)
nbreg delay_year c.novelty##i.journal_tier team_size first_author_productivity team_productivity phrase_count inter_coauthorship i.year i.field, vce(robust)
outreg2 using Supplementary_Table3.doc, append ctitle(Model 5) bdec(3) tdec(3) ///
addstat(Log-likelihood, e(ll), Wald chi2, e(chi2)) ///
addtext(Year FE, YES, Field FE, YES)

use "all-top1.dta", clear 
nbreg delay_year novelty team_size first_author_productivity team_productivity phrase_count inter_coauthorship i.year i.field, vce(robust)
outreg2 using Supplementary_Table3.doc, append ctitle(Model 6) bdec(3) tdec(3) ///
addstat(Log-likelihood, e(ll), Wald chi2, e(chi2)) ///
addtext(Year FE, YES, Field FE, YES)
nbreg delay_year c.novelty##i.journal_tier team_size first_author_productivity team_productivity phrase_count inter_coauthorship i.year i.field, vce(robust)
outreg2 using Supplementary_Table3.doc, append ctitle(Model 7) bdec(3) tdec(3) ///
addstat(Log-likelihood, e(ll), Wald chi2, e(chi2)) ///
addtext(Year FE, YES, Field FE, YES)
