# 🇨🇩 CongoLang Web: Validation Portal for Central African Languages

CongoLang is a grassroots, participatory Natural Language Processing (NLP) project dedicated to building open, high-quality, and human-validated datasets for under-resourced Central African languages (starting with Standard and Urban Lingala).

This repository contains the frontend source code for our **Cloud Validation Portal** (https://congolang.cg), an integral part of our offline-first (Sneakernet) architecture.

## 🌍 The Vision & Intent
For too long, African languages have been marginalized in the digital transition. CongoLang seeks to actively decolonize AI by ensuring **Data Sovereignty** and **Epistemic Ownership**.

1. **Prevent Digital Glottophagy:** Build parallel corpora that capture the true sociolinguistic reality of African streets (e.g., distinguishing between Standard Lingala and Kinshasa's code-switching).
2. **Participatory Research:** Native speakers are not just data providers; they are co-authors and validators of our datasets.
3. **Establish Legal Sovereignty:** Our strict "Human-in-the-loop" validation workflow, powered by Firebase Authentication, ensures our datasets meet the intellectual property protection standards of the OAPI (Bangui Agreement).

## 🏗️ Architectural Framework
Operating in regions with severe internet constraints, CongoLang bypasses traditional web-scraping (which often yields toxic or unrepresentative data) through a **Frugal, Offline-first Architecture**:

- **Data Ingestion:** Community members contribute translations locally offline.
- **Cloud Sync:** Data is securely pushed to a Google Firebase (Cloud Firestore) backend.
- **This Web Portal:** A custom-built web application where native speakers securely authenticate, peer-review, and validate AI-generated baseline translations or community submissions. *Only sentences with a `validated` status by cross-referenced human reviewers are added to the final corpus.*

## 🤝 How to Contribute
We believe in the philosophy of **Umuntu Ngumuntu Ngabantu** (I am because you are). We welcome contributors from all disciplines:

- **Linguists & Native Speakers:** Help us validate and curate the Lingala, Munukutuba, and Tshiluba datasets on our Validation Portal.
- **Developers:** Contribute to improving our Firebase backend or this web application.
- **Researchers:** Use our validated baseline data to train models and share your findings!

## 📜 License
- **Source Code:** MIT License
- **Datasets:** CC-BY-4.0 (Ensuring open academic access while protecting the community's sovereign ownership).
