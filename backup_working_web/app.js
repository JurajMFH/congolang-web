/**
 * CongoLang Landing Page - Real-time Brazzaville Clock & Firestore Crowdsourcing
 */

// --- Firebase CDN Imports (v9.22.0) ---
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/9.22.0/firebase-analytics.js";
import { getFirestore, collection, addDoc, serverTimestamp } from "https://www.gstatic.com/firebasejs/9.22.0/firebase-firestore.js";

// --- Production Firebase Configuration ---
const firebaseConfig = {
  apiKey: "AIzaSyDnuZh7hxjo_8lop5J1LjxzZ-o45_MQpr0",
  authDomain: "congolang.firebaseapp.com",
  projectId: "congolang",
  storageBucket: "congolang.firebasestorage.app",
  messagingSenderId: "823661895203",
  appId: "1:823661895203:web:f76c740256df60bbe45b96",
  measurementId: "G-Q48Q9GJ8KJ"
};

// Initialize Firebase Production Services
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
const db = getFirestore(app);


// --- Real-time Brazzaville Clock Logic ---
function updateTime() {
    const clockElement = document.getElementById('congo-clock');
    
    if (clockElement) {
        const now = new Date();
        
        const timeOptions = {
            timeZone: 'Africa/Brazzaville',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        };
        
        try {
            const formatter = new Intl.DateTimeFormat('fr-FR', timeOptions);
            clockElement.innerText = formatter.format(now);
        } catch (error) {
            console.error('Error formatting time:', error);
            const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
            const brazzavilleTime = new Date(utc + (3600000 * 1)); 
            clockElement.innerText = brazzavilleTime.toTimeString().split(' ')[0];
        }
    }
}

// --- Firestore Submission Logic ---
async function handleFormSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitBtn = document.getElementById('submit-btn');
    const statusMsg = document.getElementById('status-message');
    
    // Extract values
    const sourceLangCode = document.getElementById('source_lang').value;
    const sourceWord = document.getElementById('source_word').value.trim();
    const targetLang = document.getElementById('target_lang').value;
    const translationText = document.getElementById('translation_text').value.trim();

    if (!sourceWord) {
        statusMsg.innerText = "Erreur: Le mot source ne peut pas être vide.";
        statusMsg.classList.add("status-error");
        return;
    }

    // UI Loading State - Disable to prevent double submission
    submitBtn.disabled = true;
    submitBtn.innerText = "Traitement...";
    statusMsg.innerText = "";
    statusMsg.className = "status-message";

    // Timeout Promise (8 seconds)
    const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => {
            reject(new Error("Délai d'attente dépassé. La base de données est inaccessible."));
        }, 8000);
    });

    try {
        // Race the Firestore write against the timeout
        await Promise.race([
            addDoc(collection(db, "crowdsourced_translations"), {
                source_lang_code: sourceLangCode,
                source_word: sourceWord,
                target_lang: targetLang,
                translation_text: translationText,
                timestamp: serverTimestamp(),
                verified: false 
            }),
            timeoutPromise
        ]);

        // SUCCESS
        statusMsg.innerText = "Matondo! / Merci! Translation submitted successfully.";
        statusMsg.classList.add("status-success");
        form.reset();
    } catch (error) {
        // FAILURE (Timeout or API Error)
        console.error("Firestore Transaction Error:", error);
        
        // Critical Debug Alert for the user/lead
        alert("Erreur: " + (error.message || "Erreur inconnue"));
        
        statusMsg.innerText = "Erreur: Impossible de soumettre. Veuillez réessayer.";
        statusMsg.classList.add("status-error");
    } finally {
        // ALWAYS reset the UI regardless of success or failure
        submitBtn.disabled = false;
        submitBtn.innerText = "Soumettre";
    }
}

async function handleContactSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitBtn = document.getElementById('contact-submit-btn');
    const statusMsg = document.getElementById('contact-status-message');
    
    // Extract values
    const name = document.getElementById('contact_name').value.trim();
    const email = document.getElementById('contact_email').value.trim();
    const languages = document.getElementById('contact_languages').value.trim();
    const message = document.getElementById('contact_message').value.trim();

    // UI Loading State
    submitBtn.disabled = true;
    submitBtn.innerText = "Envoi en cours...";
    statusMsg.innerText = "";
    statusMsg.className = "status-message";

    // Timeout Promise (8 seconds)
    const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => {
            reject(new Error("Délai d'attente dépassé."));
        }, 8000);
    });

    try {
        await Promise.race([
            addDoc(collection(db, "contact_messages"), {
                name: name,
                email: email,
                languages: languages,
                message: message,
                timestamp: serverTimestamp()
            }),
            timeoutPromise
        ]);

        // SUCCESS
        statusMsg.innerText = "Message envoyé avec succès ! Matondo.";
        statusMsg.classList.add("status-success");
        alert("Message envoyé avec succès ! Nous vous contacterons bientôt.");
        form.reset();
    } catch (error) {
        console.error("Firestore Contact Error:", error);
        alert("Erreur: Impossible d'envoyer le message. " + (error.message || ""));
        statusMsg.innerText = "Erreur: Veuillez réessayer.";
        statusMsg.classList.add("status-error");
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = "Envoyer le message";
    }
}


// --- Floating Background Logic ---
const CONGO_LANGUAGES = [
    "Lingala", "Munukutuba", "Kituba", "Lari", "Vili", "Beembe", "Mbochi", 
    "Teke", "Aka", "Akwa", "Babole", "Baka", "Bongili", "Doondo", 
    "Kaamba", "Kongo", "Koyo", "Kunyi", "Punu", "Sundi", "Yombe", 
    "Bomitaba", "Likwala", "Mbere"
];

function initFloatingBackground() {
    const container = document.getElementById('floating-background');
    if (!container) return;

    // Create 30 initial floating elements
    for (let i = 0; i < 30; i++) {
        createFloatingWord(container);
    }
}

function createFloatingWord(container) {
    const span = document.createElement('span');
    const lang = CONGO_LANGUAGES[Math.floor(Math.random() * CONGO_LANGUAGES.length)];
    
    span.innerText = lang;
    span.className = 'floating-word';
    
    // Randomize position and animation
    const left = Math.random() * 100;
    const fontSize = 1 + Math.random() * 2; // 1rem to 3rem
    const duration = 15 + Math.random() * 15; // 15s to 30s
    const delay = Math.random() * -30; // Negative delay to start mid-animation
    
    span.style.left = `${left}%`;
    span.style.fontSize = `${fontSize}rem`;
    span.style.animationDuration = `${duration}s`;
    span.style.animationDelay = `${delay}s`;
    
    container.appendChild(span);
}

// --- Initialize All Components ---
// Wrapping initialization in DOMContentLoaded to ensure elements are available.
document.addEventListener('DOMContentLoaded', () => {
    // 1. Clock
    updateTime();
    setInterval(updateTime, 1000);
    
    // 2. Forms
    const translationForm = document.getElementById('translation-form');
    if (translationForm) {
        translationForm.addEventListener('submit', handleFormSubmit);
    }

    const contactForm = document.getElementById('contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', handleContactSubmit);
    }


    // 3. Floating Background
    initFloatingBackground();
});

