/*
 * Global interface translation (EN / ES).
 *
 * Elements marked with `data-i18n="key"` are translated on load and whenever
 * the language toggle is used. The choice is persisted in localStorage.
 */
const I18N = {
    en: {
        'nav.home': 'Home',
        'nav.stories': 'Stories',
        'nav.quiz': 'Quiz',
        'nav.report': 'AI Report',
        'nav.analytics': 'Analytics',
        'nav.vocabulary': 'Vocabulary',
        'nav.history': 'History',
        'nav.speak': 'Speak',
        'footer.tagline': 'AI-powered technical English practice',
        'lang.toggle': 'Español',
        'onboarding.button': 'How it works',
        'loading.report': 'Generating your AI report…',
        'loading.report.title': 'Generating your AI report',

        'home.title': 'Improve your technical English',
        'home.subtitle': 'Talk through real work situations, read interactive stories and test your grammar — with AI feedback at every step.',
        'home.cta.chat': 'Start a conversation',
        'home.cta.quiz': 'Take a quiz',
        'home.cta.stories': 'Read stories',
        'home.scenarios.title': 'Practice by scenario',
        'home.scenarios.browse': 'Browse stories',

        'quiz.title': 'Grammar Practice Quiz',
        'stories.title': 'Interactive Software Stories',
        'stories.create.title': 'Create Your Own Story',
        'vocab.title': 'Your Technical Vocabulary',
        'chat.subtitle': 'Reply in English — the AI tutor will correct your grammar and vocabulary in real time.',
        'speak.title': 'Speak with AI',
        'speak.subtitle': 'Speak in English and the AI will answer in voice. Best in Chrome or Edge.',
        'speak.voice': 'Voice reply',

        'scenario.daily_standup.title': 'Daily Standup',
        'scenario.daily_standup.desc': 'Share updates and blockers',
        'scenario.code_review.title': 'Code Review',
        'scenario.code_review.desc': 'Discuss code quality and improvements',
        'scenario.technical_interview.title': 'Technical Interview',
        'scenario.technical_interview.desc': 'Answer questions about your experience',
        'scenario.debugging_session.title': 'Debugging Session',
        'scenario.debugging_session.desc': 'Explain a problem and propose a fix',
        'scenario.project_planning.title': 'Project Planning',
        'scenario.project_planning.desc': 'Discuss requirements and timeline',
        'scenario.client_meeting.title': 'Client Meeting',
        'scenario.client_meeting.desc': 'Present technical recommendations',
        'scenario.architecture_discussion.title': 'Architecture Discussion',
        'scenario.architecture_discussion.desc': 'Talk about design and scalability',
        'scenario.deployment_issue.title': 'Deployment Issue',
        'scenario.deployment_issue.desc': 'Communicate an incident clearly'
    },
    es: {
        'nav.home': 'Inicio',
        'nav.stories': 'Historias',
        'nav.quiz': 'Cuestionario',
        'nav.report': 'Informe IA',
        'nav.analytics': 'Analítica',
        'nav.vocabulary': 'Vocabulario',
        'nav.history': 'Historial',
        'nav.speak': 'Conversar',
        'footer.tagline': 'Práctica de inglés técnico con IA',
        'lang.toggle': 'English',
        'onboarding.button': 'Cómo funciona',
        'loading.report': 'Generando tu informe de IA…',
        'loading.report.title': 'Generando tu informe de IA',

        'home.title': 'Mejora tu inglés técnico',
        'home.subtitle': 'Habla sobre situaciones reales de trabajo, lee historias interactivas y pon a prueba tu gramática — con feedback de IA en cada paso.',
        'home.cta.chat': 'Iniciar conversación',
        'home.cta.quiz': 'Hacer cuestionario',
        'home.cta.stories': 'Leer historias',
        'home.scenarios.title': 'Practica por escenario',
        'home.scenarios.browse': 'Ver historias',

        'quiz.title': 'Cuestionario de gramática',
        'stories.title': 'Historias interactivas de software',
        'stories.create.title': 'Crea tu propia historia',
        'vocab.title': 'Tu vocabulario técnico',
        'chat.subtitle': 'Responde en inglés — el tutor de IA corregirá tu gramática y vocabulario en tiempo real.',
        'speak.title': 'Conversar con IA',
        'speak.subtitle': 'Habla en inglés y la IA te responderá en voz. Funciona mejor en Chrome o Edge.',
        'speak.voice': 'Respuesta por voz',

        'scenario.daily_standup.title': 'Reunión diaria',
        'scenario.daily_standup.desc': 'Comparte avances y bloqueos',
        'scenario.code_review.title': 'Revisión de código',
        'scenario.code_review.desc': 'Analiza la calidad del código',
        'scenario.technical_interview.title': 'Entrevista técnica',
        'scenario.technical_interview.desc': 'Responde sobre tu experiencia',
        'scenario.debugging_session.title': 'Sesión de depuración',
        'scenario.debugging_session.desc': 'Explica un problema y propón una solución',
        'scenario.project_planning.title': 'Planificación de proyecto',
        'scenario.project_planning.desc': 'Habla de requisitos y plazos',
        'scenario.client_meeting.title': 'Reunión con cliente',
        'scenario.client_meeting.desc': 'Presenta recomendaciones técnicas',
        'scenario.architecture_discussion.title': 'Discusión de arquitectura',
        'scenario.architecture_discussion.desc': 'Habla de diseño y escalabilidad',
        'scenario.deployment_issue.title': 'Problema de despliegue',
        'scenario.deployment_issue.desc': 'Comunica un incidente con claridad'
    }
};

function currentLang() {
    return localStorage.getItem('lang') === 'es' ? 'es' : 'en';
}

function applyLang(lang) {
    localStorage.setItem('lang', lang);
    document.documentElement.lang = lang;

    document.querySelectorAll('[data-i18n]').forEach((el) => {
        const key = el.getAttribute('data-i18n');
        const value = I18N[lang] && I18N[lang][key];
        if (value) el.textContent = value;
    });

    const toggleLabel = lang === 'es' ? 'English' : 'Español';
    document.querySelectorAll('.js-lang-label').forEach((el) => {
        el.textContent = toggleLabel;
    });
}

function toggleLang() {
    applyLang(currentLang() === 'es' ? 'en' : 'es');
}

document.addEventListener('DOMContentLoaded', () => applyLang(currentLang()));
