import json
import time
import re
from typing import Dict, Any, List, Optional
from playwright.sync_api import sync_playwright, Page, BrowserContext
from src.logger import get_logger
from src.ai.solver import QuestionSolver

logger = get_logger("naukri_cdp")

class NaukriCDPAutomator:
    """Automates real job scanning and application on Naukri via Chrome Remote Debugging (CDP)."""

    def __init__(self, cdp_url: str = "http://localhost:9222"):
        self.cdp_url = cdp_url
        self.browser = None
        self.context = None
        self.page = None

    def connect(self) -> Dict[str, Any]:
        """Connects to the open Chrome instance over CDP."""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.connect_over_cdp(self.cdp_url)
            
            # Find existing contexts and pages
            contexts = self.browser.contexts
            if not contexts:
                return {"success": False, "error": "No browser contexts found. Make sure Chrome is open."}
            
            self.context = contexts[0]
            pages = self.context.pages
            
            # Find an active Naukri tab or pick the current page
            naukri_pages = [p for p in pages if "naukri.com" in p.url]
            if naukri_pages:
                self.page = naukri_pages[0]
            elif pages:
                self.page = pages[0]
            else:
                self.page = self.context.new_page()
                self.page.goto("https://www.naukri.com")

            return {
                "success": True,
                "url": self.page.url,
                "title": self.page.title(),
                "open_tabs": len(pages)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def is_logged_in(self) -> bool:
        """Checks if the user is currently logged into Naukri."""
        if not self.page:
            return False
        try:
            # Check for profile icon, nI-gNb-drawer, or logout indicator
            profile_selectors = [
                ".nI-gNb-drawer", 
                "div.view-profile-wrapper", 
                "a[href*='mnjuser/profile']",
                ".user-profile-icon",
                ".profile-summary"
            ]
            for sel in profile_selectors:
                if self.page.query_selector(sel):
                    return True
            # Alternative: check if "Login" button is absent
            login_btn = self.page.query_selector("#login_Layer, a.login_Layer")
            return login_btn is None and "naukri.com" in self.page.url
        except Exception:
            return False

    def scan_jobs_on_page(self) -> List[Dict[str, Any]]:
        """Extracts job cards displayed on the current Naukri page."""
        if not self.page:
            return []

        jobs = []
        try:
            # Support both Recommended Jobs (.jobTuple) and Search Results (.srp-jobtuple-wrapper, article.jobTuple)
            cards = self.page.query_selector_all(".jobTuple, .srp-jobtuple-wrapper, article.jobTuple, div.cust-job-tuple")
            for idx, card in enumerate(cards):
                try:
                    # Title: <p class="title"> or <a class="title">
                    title_elem = card.query_selector("p.title, a.title, .title, a.job-title")
                    title = title_elem.inner_text().strip() if title_elem else "Software Engineer"
                    
                    url = ""
                    if title_elem and title_elem.evaluate("el => el.tagName.toLowerCase()") == "a":
                        cand_url = title_elem.get_attribute("href") or ""
                        if "job-listings" in cand_url or "naukri.com" in cand_url:
                            url = cand_url
                    
                    if not url:
                        link_elem = card.query_selector("a[href*='job-listings'], a[href*='naukri.com/job']")
                        if link_elem:
                            url = link_elem.get_attribute("href") or ""

                    # Company: .subTitle, a.comp-name, a.companyName
                    comp_elem = card.query_selector(".subTitle, a.comp-name, a.companyName")
                    if not comp_elem:
                        comp_elem = card.query_selector(".companyWrapper")
                    
                    company = "Confidential"
                    if comp_elem:
                        company = comp_elem.get_attribute("title") or comp_elem.inner_text().strip()
                        company = company.split("\n")[0].strip()

                    # Experience: .experience, .expwdth
                    exp_elem = card.query_selector(".experience, .expwdth")
                    experience = exp_elem.inner_text().strip() if exp_elem else ""

                    # Location: .location, .locWdth
                    loc_elem = card.query_selector(".location, .locWdth")
                    location = loc_elem.inner_text().strip() if loc_elem else "Bengaluru"

                    # Description snippet
                    desc_elem = card.query_selector(".job-description, .job-desc, .ellipsis")
                    desc_text = desc_elem.inner_text().strip() if desc_elem else ""

                    # Tags / Skills
                    tags_elems = card.query_selector_all(".tags li, .tag-li, .tags-gt li, ul.tags li")
                    tags = [t.inner_text().strip() for t in tags_elems if t.inner_text().strip()]

                    # Check for quick apply / checkbox
                    checkbox = card.query_selector(".tuple-check-box, .naukicon-ot-checkbox")
                    apply_btn = card.query_selector("button.apply-button, .easy-apply")
                    is_direct_apply = (checkbox is not None) or (apply_btn is not None)

                    job_id_attr = card.get_attribute("data-job-id")
                    if not job_id_attr and url:
                        match = re.search(r"-(\d{6,})", url)
                        job_id_attr = match.group(1) if match else f"NAUKRI-{idx+1}"
                    elif not job_id_attr:
                        job_id_attr = f"NAUKRI-{idx+1}"

                    # Construct proper direct Naukri job URL if missing or non-naukri
                    if not url or "naukri.com" not in url:
                        url = f"https://www.naukri.com/job-listings-{job_id_attr}"

                    full_desc = f"{title} at {company}. {desc_text}. Skills: {', '.join(tags)}."

                    jobs.append({
                        "job_id": str(job_id_attr),
                        "title": title,
                        "company": company,
                        "experience": experience,
                        "location": location,
                        "tech_skills": ", ".join(tags),
                        "description": full_desc,
                        "url": url,
                        "platform": "Naukri",
                        "is_direct_apply": is_direct_apply
                    })
                except Exception:
                    continue
        except Exception as e:
            print(f"Error reading job cards: {e}")

        return jobs

    def apply_to_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Navigates to or clicks apply on a Naukri job."""
        if not self.page:
            return {"success": False, "reason": "No active page"}

        try:
            url = job.get("url")
            if url:
                # Open in current tab or new tab
                self.page.goto(url, timeout=30000)
                time.sleep(2)

                # Look for the main Apply / I am Interested button
                apply_button_selectors = [
                    "button#apply-button",
                    "button.apply-button",
                    "button:has-text('Apply')",
                    "button:has-text('I am interested')",
                    "#already-applied"
                ]

                for sel in apply_button_selectors:
                    btn = self.page.query_selector(sel)
                    if btn:
                        btn_text = btn.inner_text().strip().lower()
                        if "applied" in btn_text:
                            return {"success": True, "status": "ALREADY_APPLIED", "reason": "Already marked as applied on portal"}
                        
                        btn.click()
                        time.sleep(2)
                        
                        # Check if a modal or chatbot opened
                        # Often Naukri has a 1-click apply or question prompts
                        return {"success": True, "status": "APPLIED", "reason": "Application submitted successfully"}

            return {"success": False, "status": "FAILED", "reason": "Apply button not clickable or external portal"}
        except Exception as e:
            return {"success": False, "status": "ERROR", "reason": str(e)}

    def batch_apply_recommended_jobs(self, min_match_score: float = 65.0, max_limit: int = 5) -> Dict[str, Any]:
        """
        Selects up to 5 matching jobs on the Recommended Jobs page using checkboxes,
        and clicks the 'Apply X Jobs' button (.multi-apply-button).
        """
        if not self.page:
            return {"success": False, "applied_count": 0, "error": "No active page connected"}

        try:
            from src.parser import ProfileManager
            from src.matcher import JobMatcher
            profile = ProfileManager("profile.json")
            matcher = JobMatcher(profile)

            # Find all job cards on current page
            cards = self.page.query_selector_all(".jobTuple")
            if not cards:
                return {"success": False, "applied_count": 0, "error": "No .jobTuple cards found on current page"}

            selected_jobs = []
            checked_count = 0

            for card in cards:
                if checked_count >= max_limit:
                    break

                # Check if already applied or hidden
                card_text = card.inner_text().lower()
                if "applied" in card_text:
                    continue

                # Extract basic info & score
                title_elem = card.query_selector(".title")
                title = title_elem.inner_text().strip() if title_elem else "Software Engineer"
                
                comp_elem = card.query_selector(".subTitle")
                comp = comp_elem.inner_text().strip().split("\n")[0] if comp_elem else "Confidential"

                tags_elems = card.query_selector_all(".tags li")
                tags = [t.inner_text().strip() for t in tags_elems if t.inner_text().strip()]

                job_data = {
                    "title": title,
                    "company": comp,
                    "description": f"{title} at {comp}. Skills: {', '.join(tags)}.",
                    "platform": "Naukri"
                }

                matcher.calculate_match_score(job_data)
                score = job_data.get("match_score", 0)

                # Only select if score meets candidate criteria
                if score >= min_match_score:
                    cb = card.query_selector(".tuple-check-box, .naukicon-ot-checkbox")
                    if cb:
                        # Scroll into view and click
                        cb.scroll_into_view_if_needed()
                        time.sleep(0.3)
                        cb.click()
                        checked_count += 1
                        job_data["job_id"] = card.get_attribute("data-job-id") or f"NAUKRI-{checked_count}"
                        selected_jobs.append(job_data)
                        time.sleep(0.4)

            if checked_count == 0:
                return {
                    "success": True,
                    "applied_count": 0,
                    "message": f"No unapplied jobs met the minimum match score of {min_match_score}%."
                }

            # Wait briefly for batch button text to update e.g. "Apply 3 Jobs"
            time.sleep(0.8)

            # Click the batch apply button
            multi_apply_btn = self.page.query_selector("button.multi-apply-button, .multi-apply-button")
            if not multi_apply_btn:
                multi_apply_btn = self.page.query_selector("button:has-text('Apply')")

            if multi_apply_btn:
                multi_apply_btn.scroll_into_view_if_needed()
                time.sleep(0.5)
                multi_apply_btn.click()
                time.sleep(2.0)

                # Check if Recruiter Question / Chatbot modal popped up
                self._handle_chatbot_prompts()

                return {
                    "success": True,
                    "applied_count": checked_count,
                    "jobs": selected_jobs,
                    "message": f"Successfully applied to {checked_count} jobs in batch!"
                }
            else:
                return {
                    "success": False,
                    "applied_count": 0,
                    "error": "Checked jobs but could not locate .multi-apply-button"
                }

        except Exception as e:
            return {"success": False, "applied_count": 0, "error": str(e)}

    def _handle_chatbot_prompts(self, solver: Optional[QuestionSolver] = None, max_prompts: int = 4):
        """Detects and answers interactive recruiter chatbot / questionnaire prompts using AI solver."""
        if not self.page:
            return

        if not solver:
            try:
                solver = QuestionSolver()
            except Exception as e:
                logger.warning(f"Could not initialize QuestionSolver: {e}")

        for step in range(max_prompts):
            try:
                # Check if chatbot / question modal exists
                save_btn = self.page.query_selector("button:has-text('Save'), .bot-save, button.waves-effect:has-text('Save'), button:has-text('Submit')")
                if not save_btn:
                    break

                # Extract question label text from modal
                q_elem = self.page.query_selector(".bot-question, .modal-title, .question-text, label.bot-label, div[class*='question']")
                q_text = q_elem.inner_text().strip() if q_elem else "Recruiter screening question"
                logger.info(f"🤖 Recruiter Prompt Detected [{step+1}/{max_prompts}]: '{q_text}'")

                # Handle radio choices e.g. Yes/No
                radio_options = self.page.query_selector_all("label:has-text('Yes'), label:has-text('No'), .radio-wrap")
                if radio_options:
                    opts_text = [r.inner_text().strip() for r in radio_options]
                    solution = solver.solve_question(q_text, field_type="radio", options=opts_text) if solver else {"answer": "Yes"}
                    target_ans = solution.get("answer", "Yes")
                    logger.info(f"  -> AI Decision ({solution.get('source', 'fallback')}): Selected '{target_ans}'")

                    clicked = False
                    for r in radio_options:
                        if target_ans.lower() in r.inner_text().strip().lower():
                            r.click()
                            clicked = True
                            break
                    if not clicked and radio_options:
                        radio_options[0].click()
                    time.sleep(0.4)

                # Handle text / numeric input fields
                num_input = self.page.query_selector("input[type='number'], input[type='text'], input.bot-input, textarea")
                if num_input and not num_input.input_value():
                    solution = solver.solve_question(q_text, field_type="text") if solver else {"answer": "4.5"}
                    val = str(solution.get("answer", "4.5"))
                    logger.info(f"  -> AI Decision ({solution.get('source', 'fallback')}): Filling '{val}'")
                    num_input.fill(val)
                    time.sleep(0.3)

                # Click Save / Submit button
                if save_btn.is_enabled():
                    save_btn.click()
                    logger.info("  -> Saved prompt answer cleanly.")
                    time.sleep(1.5)
                else:
                    break
            except Exception as e:
                logger.warning(f"Error handling chatbot prompt: {e}")
                break

    def close(self):
        """Disconnects cleanly without closing user's Chrome."""
        try:
            if self.browser:
                self.browser.close()
            if hasattr(self, "playwright") and self.playwright:
                self.playwright.stop()
        except Exception:
            pass

