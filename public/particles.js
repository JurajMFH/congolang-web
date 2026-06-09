/**
 * CongoLang Interactive Particle Network Background
 * Renders Congo languages and platform logos on a canvas with interactive connection lines.
 */

(function () {
    const canvas = document.getElementById('particleCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let particles = [];
    const mouse = { x: 0, y: 0, active: false };

    // --- Configuration ---
    const MAX_LINE_DIST = 140; // Max distance to draw lines between particles
    const MOUSE_LINE_DIST = 170; // Max distance to connect lines to mouse
    const BASE_OPACITY = 0.12; // Base opacity for elements
    
    const LANGUAGES = [
        "Lingala", "Munukutuba", "Kituba", "Lari", "Vili", 
        "Beembe", "Mbochi", "Teke", "Aka", "Kongo", 
        "Kunyi", "Sundi", "Yombe", "Swahili", "Tshiluba"
    ];

    // SVG paths from the original icons (viewbox assumed to be 0 0 24 24, centered around 12,12)
    const LOGO_PATHS = {
        tiktok: new Path2D("M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.02 1.62 4.17.94.99 2.26 1.62 3.69 1.76v3.91c-1.39-.02-2.74-.47-3.89-1.28a7.846 7.846 0 0 1-2.92-3.66v9.33c.07 1.54-.38 3.12-1.3 4.36-1.57 2.22-4.52 3.15-7.14 2.24-2.61-.84-4.47-3.41-4.48-6.15.01-2.97 2.23-5.59 5.17-5.99.99-.15 2-.04 2.94.31v4.09c-.73-.42-1.58-.58-2.42-.42-1.44.22-2.58 1.48-2.62 2.94-.07 1.83 1.52 3.44 3.36 3.42 1.79.03 3.36-1.38 3.42-3.17.02-.63.01-11.45.01-11.45z"),
        linkedin: new Path2D("M22.23 0H1.77C.8 0 0 .77 0 1.72v20.56C0 23.23.8 24 1.77 24h20.46c.98 0 1.77-.77 1.77-1.72V1.72C24 .77 23.2 0 22.23 0zM7.12 20.45H3.56V9H7.12v11.45zM5.34 7.43c-1.14 0-2.06-.92-2.06-2.06 0-1.14.92-2.06 2.06-2.06 1.14 0 2.06.92 2.06 2.06 0 1.14-.92 2.06-2.06 2.06zm15.11 13.02h-3.56v-5.6c0-1.34-.03-3.05-1.86-3.05-1.86 0-2.14 1.45-2.14 2.95v5.7H9.33V9h3.42v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.45v6.29z"),
        youtube: new Path2D("M23.498 6.163a3.003 3.003 0 0 0-2.11-2.11C19.517 3.545 12 3.545 12 3.545s-7.516 0-9.387.508a3.003 3.003 0 0 0-2.11 2.11C0 8.033 0 12 0 12s0 3.967.502 5.837a3.003 3.003 0 0 0 2.11 2.11c1.871.508 9.387.508 9.387.508s7.517 0 9.387-.508a3.003 3.003 0 0 0 2.11-2.11C24 15.967 24 12 24 12s0-3.967-.502-5.837zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"),
        github: new Path2D("M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.462-1.11-1.462-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.579.688.481C19.137 20.162 22 16.418 22 12c0-5.523-4.477-10-10-10z"),
        facebook: new Path2D("M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"),
        instagram: new Path2D("M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.051.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 1 0 0 12.324 6.162 6.162 0 0 0 0-12.324zM12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm6.406-11.845a1.44 1.44 0 1 0 0 2.881 1.44 1.44 0 0 0 0-2.881z"),
        snapchat: new Path2D("M12 .03c-2.483 0-4.088 1.139-4.757 2.478-.178.356-.16.711-.062 1.067a6.837 6.837 0 0 0 1.245 2.134 5.922 5.922 0 0 1-.951.81c-.562.373-.801.765-.801 1.342 0 .436.213.783.587 1.022.373.24.871.32 1.423.231.142-.022.302-.058.462-.1.08.35.213.676.383.978.275.498.667.871 1.182 1.102.507.231 1.094.32 1.77.267v.462c0 .48-.09.916-.276 1.298-.186.373-.453.685-.809.934-.356.248-.791.435-1.298.56-.507.124-1.076.195-1.698.213-.622.018-1.289.018-2.001-.009-.436-.018-.756.09-1.013.267-.258.178-.382.49-.382.907v.142c0 .64.24 1.094.72 1.343.48.248 1.156.328 2.018.239.862-.088 1.832-.39 2.899-.897.124-.053.257-.098.39-.125.133-.026.249.027.356.16a5.795 5.795 0 0 0 1.013 1.049c.471.39.996.587 1.574.587a2.028 2.028 0 0 0 1.574-.587 5.795 5.795 0 0 0 1.013-1.049c.107-.133.223-.186.356-.16a2.802 2.802 0 0 0 .39.125c1.067.507 2.036.809 2.899.897.862.089 1.538.009 2.018-.239.48-.249.72-.703.72-1.343v-.142c0-.417-.124-.729-.382-.907-.257-.177-.577-.285-1.013-.267-.712.027-1.379.027-2.001.009-.507-.018-.942-.089-1.698-.213-.356-.058-.693-.16-1.023-.311v-.978c-.356-.249-.622-.56-.809-.934-.186-.382-.276-.818-.276-1.298v-.462c.676.053 1.263-.036 1.77-.267.515-.231.907-.604 1.182-1.102.17-.302.303-.628.383-.978.16.042.32.078.462.1.552.089 1.05.009 1.423-.231.374-.239.587-.586.587-1.022 0-.577-.239-.969-.801-1.342-.267-.178-.587-.449-.951-.81a6.837 6.837 0 0 0 1.245-2.134c.098-.356.116-.711.062-1.067C16.088 1.169 14.483.03 12 .03z"),
        x: new Path2D("M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"),
        slack: new Path2D("M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523 2.528 2.528 0 0 1-2.522-2.523 2.528 2.528 0 0 1 2.522-2.52h2.52v2.52zm1.261 0a2.528 2.528 0 0 1 2.52-2.52h5.043a2.528 2.528 0 0 1 2.522 2.52v5.042a2.528 2.528 0 0 1-2.522 2.52H8.823a2.528 2.528 0 0 1-2.52-2.52v-5.042zM8.823 5.043a2.528 2.528 0 0 1 2.52-2.52 2.528 2.528 0 0 1 2.522 2.52v2.52h-2.522a2.528 2.528 0 0 1-2.52-2.52zm0 1.261a2.528 2.528 0 0 1 2.52 2.52v5.043a2.528 2.528 0 0 1-2.522 2.522H3.78a2.528 2.528 0 0 1-2.522-2.522 2.528 2.528 0 0 1 2.522-2.52h5.043zm10.135 3.696a2.528 2.528 0 0 1 2.522-2.52 2.528 2.528 0 0 1 2.52 2.52 2.528 2.528 0 0 1-2.52 2.522h-2.522V10zm-1.262 0a2.528 2.528 0 0 1-2.52 2.52h-5.043a2.528 2.528 0 0 1-2.522-2.52V4.958a2.528 2.528 0 0 1 2.522-2.52h5.043a2.528 2.528 0 0 1 2.52 2.52v5.042zm-3.781 10.121a2.528 2.528 0 0 1-2.52 2.52 2.528 2.528 0 0 1-2.522-2.52v-2.52h2.522a2.528 2.528 0 0 1 2.52 2.52zm0-1.262a2.528 2.528 0 0 1-2.52-2.52v-5.043a2.528 2.528 0 0 1 2.522-2.522h5.043a2.528 2.528 0 0 1 2.522 2.522v5.043a2.528 2.528 0 0 1-2.522 2.52h-5.043z"),
        huggingface: new Path2D("M12 22a10 10 0 1 1 10-10 10.011 10.011 0 0 1-10 10zm0-18a8 8 0 1 0 8 8 8.01 8.01 0 0 0-8-8zm4.5 9a.5.5 0 0 1 .5.5 4.5 4.5 0 0 1-9 0 .5.5 0 0 1 1 0 3.5 3.5 0 0 0 7 0 .5.5 0 0 1 .5-.5zM9 10a1 1 0 1 1-1 1 1 1 0 0 1 1-1zm6 0a1 1 0 1 1-1 1 1 1 0 0 1 1-1z")
    };
    const LOGO_KEYS = Object.keys(LOGO_PATHS);

    class Particle {
        constructor() {
            this.reset(true);
        }

        reset(initial = false) {
            this.type = Math.random() < 0.55 ? 'word' : 'logo'; // 55% text, 45% logo
            
            if (this.type === 'word') {
                this.content = LANGUAGES[Math.floor(Math.random() * LANGUAGES.length)];
                this.fontSize = 12 + Math.random() * 10; // 12px to 22px
                // Set width / height estimate for boundary check
                this.width = ctx.measureText(this.content).width || (this.fontSize * 5);
                this.height = this.fontSize;
            } else {
                this.content = LOGO_KEYS[Math.floor(Math.random() * LOGO_KEYS.length)];
                this.logoSize = 16 + Math.random() * 12; // 16px to 28px
                this.width = this.logoSize;
                this.height = this.logoSize;
            }

            // Margin to spawn inside screen
            const pad = 40;
            if (initial) {
                this.x = Math.random() * (canvas.width - pad * 2) + pad;
                this.y = Math.random() * (canvas.height - pad * 2) + pad;
            } else {
                // Spawn on a random edge
                if (Math.random() < 0.5) {
                    this.x = Math.random() < 0.5 ? -pad : canvas.width + pad;
                    this.y = Math.random() * canvas.height;
                } else {
                    this.x = Math.random() * canvas.width;
                    this.y = Math.random() < 0.5 ? -pad : canvas.height + pad;
                }
            }

            // Direction and Speed
            const angle = Math.random() * Math.PI * 2;
            const speed = 0.2 + Math.random() * 0.5; // 0.2 to 0.7 speed
            this.vx = Math.cos(angle) * speed;
            this.vy = Math.sin(angle) * speed;
            this.baseSpeed = speed;

            // Opacity & Color
            this.opacity = BASE_OPACITY * (0.6 + Math.random() * 0.8); // slight variation
        }

        update() {
            // Apply mouse attraction force if active and close
            if (mouse.active) {
                const dx = mouse.x - this.x;
                const dy = mouse.y - this.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 180) {
                    // Pull force increases as distance decreases, max force at 0
                    const force = (180 - dist) / 180 * 0.04;
                    this.vx += (dx / dist) * force;
                    this.vy += (dy / dist) * force;
                }
            }

            // Friction/damping to prevent velocity explosion from mouse pull
            this.vx *= 0.98;
            this.vy *= 0.98;

            // Ensure speed is within bounds
            const currentSpeed = Math.sqrt(this.vx * this.vx + this.vy * this.vy);
            if (currentSpeed > 2.0) {
                this.vx = (this.vx / currentSpeed) * 2.0;
                this.vy = (this.vy / currentSpeed) * 2.0;
            } else if (currentSpeed < 0.15) {
                // Steer in a random angle to keep it moving
                const angle = Math.random() * Math.PI * 2;
                this.vx = Math.cos(angle) * this.baseSpeed;
                this.vy = Math.sin(angle) * this.baseSpeed;
            }

            // Move
            this.x += this.vx;
            this.y += this.vy;

            // Out-of-bounds wrap or reset
            const pad = 60;
            if (this.x < -pad || this.x > canvas.width + pad || this.y < -pad || this.y > canvas.height + pad) {
                this.reset(false);
            }
        }

        draw() {
            ctx.fillStyle = `rgba(17, 17, 17, ${this.opacity})`;
            
            if (this.type === 'word') {
                ctx.font = `bold ${this.fontSize}px 'Inter', system-ui, -apple-system, sans-serif`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(this.content, this.x, this.y);
            } else {
                const path = LOGO_PATHS[this.content];
                if (path) {
                    ctx.save();
                    ctx.translate(this.x, this.y);
                    // Standard path viewBox is 24x24, center is (12, 12)
                    const scale = this.logoSize / 24;
                    ctx.scale(scale, scale);
                    ctx.translate(-12, -12);
                    ctx.fill(path);
                    ctx.restore();
                }
            }
        }
    }

    function resizeCanvas() {
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        
        ctx.scale(dpr, dpr);
        
        // Correct internal canvas size tracking matches logical viewport size
        canvas.width = rect.width;
        canvas.height = rect.height;

        initParticles();
    }

    function initParticles() {
        // Compute count based on window size to prevent cluttering / blankness
        const count = Math.min(45, Math.floor((canvas.width * canvas.height) / 22000));
        
        // Populate or adjust existing array
        if (particles.length === 0) {
            for (let i = 0; i < count; i++) {
                particles.push(new Particle());
            }
        } else if (particles.length > count) {
            particles = particles.slice(0, count);
        } else {
            while (particles.length < count) {
                particles.push(new Particle());
            }
        }
    }

    function drawLines() {
        for (let i = 0; i < particles.length; i++) {
            const p1 = particles[i];
            
            // Connect to other particles
            for (let j = i + 1; j < particles.length; j++) {
                const p2 = particles[j];
                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < MAX_LINE_DIST) {
                    // Line opacity scales inverse with distance
                    const lineOpacity = (1 - dist / MAX_LINE_DIST) * 0.07;
                    ctx.strokeStyle = `rgba(17, 17, 17, ${lineOpacity})`;
                    ctx.lineWidth = 0.8;
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }
            }

            // Connect to mouse cursor
            if (mouse.active) {
                const dx = p1.x - mouse.x;
                const dy = p1.y - mouse.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < MOUSE_LINE_DIST) {
                    const lineOpacity = (1 - dist / MOUSE_LINE_DIST) * 0.12;
                    ctx.strokeStyle = `rgba(17, 17, 17, ${lineOpacity})`;
                    ctx.lineWidth = 1.0;
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(mouse.x, mouse.y);
                    ctx.stroke();
                }
            }
        }
    }

    function animate() {
        // Clear screen with a slight transparency for a subtle motion trail (optional, but clean clear is safer)
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Update physics and position
        particles.forEach(p => p.update());

        // Render connection networks
        drawLines();

        // Render nodes
        particles.forEach(p => p.draw());

        requestAnimationFrame(animate);
    }

    // --- Interactive Mouse Handlers ---
    window.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        mouse.x = e.clientX - rect.left;
        mouse.y = e.clientY - rect.top;
        mouse.active = true;
    });

    window.addEventListener('mouseleave', () => {
        mouse.active = false;
    });

    // Touch support for mobile devices
    window.addEventListener('touchmove', (e) => {
        if (e.touches.length > 0) {
            const rect = canvas.getBoundingClientRect();
            mouse.x = e.touches[0].clientX - rect.left;
            mouse.y = e.touches[0].clientY - rect.top;
            mouse.active = true;
        }
    });

    window.addEventListener('touchend', () => {
        mouse.active = false;
    });

    // --- Engine Initialization ---
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();
    animate();
})();
