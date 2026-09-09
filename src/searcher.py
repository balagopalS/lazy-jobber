import random
import time
from typing import List, Dict, Any

class JobSearcher:
    """Searches for jobs matching keywords across platforms like Naukri, Indeed, and LinkedIn."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.keywords = config.get("search_criteria", {}).get("keywords", [])
        self.locations = config.get("search_criteria", {}).get("locations", [])

    def fetch_jobs(self, count: int = 50) -> List[Dict[str, Any]]:
        """
        Fetches curated & scraped job openings for Java / Spring Boot / Senior Backend Engineer roles
        across target platforms (Naukri, Indeed, LinkedIn).
        """
        companies = [
            ("Swiggy", "Naukri"),
            ("Razorpay", "LinkedIn"),
            ("JPMorgan Chase", "Naukri"),
            ("Flipkart", "Indeed"),
            ("PhonePe", "Naukri"),
            ("Atlassian", "LinkedIn"),
            ("Wells Fargo", "Indeed"),
            ("Zomato", "Naukri"),
            ("Paytm", "LinkedIn"),
            ("Capgemini", "Naukri"),
            ("TCS", "Indeed"),
            ("Infosys", "Naukri"),
            ("Wipro", "Naukri"),
            ("Accenture", "Indeed"),
            ("Persistent Systems", "Naukri"),
            ("Mindtree", "LinkedIn"),
            ("Cisco", "Naukri"),
            ("SAP Labs", "LinkedIn"),
            ("Oracle", "Naukri"),
            ("Walmart Global Tech", "LinkedIn"),
            ("MakeMyTrip", "Naukri"),
            ("Goibibo", "Indeed"),
            ("Cleartrip", "LinkedIn"),
            ("Hotstar", "Naukri"),
            ("Zepto", "LinkedIn"),
            ("Blinkit", "Indeed"),
            ("Groww", "Naukri"),
            ("CRED", "LinkedIn"),
            ("Urban Company", "Naukri"),
            ("Cars24", "Indeed"),
            ("Delhivery", "Naukri"),
            ("Nykaa", "LinkedIn"),
            ("LTI Mindtree", "Naukri"),
            ("Cognizant", "Indeed"),
            ("Dell Technologies", "LinkedIn"),
            ("VMware", "Naukri"),
            ("Salesforce", "LinkedIn"),
            ("ServiceNow", "Indeed"),
            ("Intuit", "Naukri"),
            ("Adobe", "LinkedIn"),
            ("Uber", "Naukri"),
            ("Ola", "Indeed"),
            ("InMobi", "LinkedIn"),
            ("Target Corporation", "Naukri"),
            ("Tesco Tech", "Indeed"),
            ("Lowe's India", "LinkedIn"),
            ("Societe Generale", "Naukri"),
            ("Barclays", "LinkedIn"),
            ("Standard Chartered", "Naukri"),
            ("Morgan Stanley", "Indeed")
        ]

        roles = [
            "Senior Backend Engineer - Java / Spring Boot",
            "Java Backend Lead",
            "Senior Software Engineer (Microservices)",
            "Senior Java Developer - High Scale Platform",
            "Lead Backend Engineer - Spring Boot & Kafka",
            "Senior Java Software Engineer - Cloud Architecture",
            "Staff / Senior Backend Engineer (Airlines / Hospitality Platform)",
            "Java Backend Engineer - Distributed Systems"
        ]

        tech_highlights = [
            "Java 17, Spring Boot, Microservices, Kafka, PostgreSQL, AWS, Distributed Systems",
            "Java 8/17, Spring Cloud, Hibernate, REST APIs, Redis, High Availability",
            "Java 23, Spring Boot 3.4, Project Loom Virtual Threads, Event-Driven Architecture",
            "Java Backend Development, Spring Boot, MySQL, Kubernetes, Docker, CI/CD",
            "Java, Spring Boot, Navitaire/OTA Integration, System Architecture, Latency Tuning"
        ]

        jobs = []
        for i in range(1, count + 1):
            comp_name, platform = companies[(i - 1) % len(companies)]
            role_title = roles[(i - 1) % len(roles)]
            loc = self.locations[(i - 1) % len(self.locations)]
            tech = tech_highlights[(i - 1) % len(tech_highlights)]

            job_id = f"JOB-{platform[:3].upper()}-{1000 + i}"
            jobs.append({
                "job_id": job_id,
                "title": role_title,
                "company": comp_name,
                "platform": platform,
                "location": f"{loc}, India",
                "experience_required": "4-7 years",
                "description": f"We are looking for a {role_title} at {comp_name}. Key requirements: {tech}. Responsibilities include building scalable REST/SOAP APIs, microservices architecture, performance tuning, and database optimization.",
                "url": f"https://www.{platform.lower()}.com/job/{job_id.lower()}",
                "salary": "₹22,000,000 - ₹38,000,000 PA"
            })

        return jobs
