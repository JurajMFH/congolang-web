const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const REPORT_FILE = 'congolang_web_state_report.md';
const PUBLIC_DIR = 'public';
const WORKFLOWS_DIR = '.github/workflows';

/**
 * Executes a shell command and returns the output.
 * Gracefully handles errors to avoid script crashes.
 */
function runCommand(command) {
    try {
        // Add --non-interactive to all firebase commands
        const cmd = command.includes('firebase') ? `${command} --non-interactive` : command;
        return execSync(cmd, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
    } catch (error) {
        return `[ERROR] Failed to execute: ${command}\n${error.message}`;
    }
}

/**
 * Audits PWA and Offline readiness.
 */
function auditPWA() {
    const swPath = path.join(PUBLIC_DIR, 'service-worker.js');
    const manifestPath = path.join(PUBLIC_DIR, 'manifest.json');
    const appJsPath = path.join(PUBLIC_DIR, 'app.js');

    let report = '### PWA & Offline Readiness\n\n';
    
    // Check Service Worker
    if (fs.existsSync(swPath)) {
        const swContent = fs.readFileSync(swPath, 'utf8');
        report += `- [x] **Service Worker**: Found at \`${swPath}\`.\n`;
        report += swContent.includes('cache.addAll') 
            ? '  - [x] Static assets caching implemented.\n' 
            : '  - [ ] Static assets caching NOT found.\n';
    } else {
        report += '- [ ] **Service Worker**: MISSING. Offline support will be limited.\n';
    }

    // Check Manifest
    if (fs.existsSync(manifestPath)) {
        report += `- [x] **Manifest**: Found at \`${manifestPath}\`.\n`;
    } else {
        report += '- [ ] **Manifest**: MISSING. Application cannot be installed as a PWA.\n';
    }

    // Check IndexedDB (User requirement)
    if (fs.existsSync(appJsPath)) {
        const appJsContent = fs.readFileSync(appJsPath, 'utf8');
        if (appJsContent.includes('indexedDB') || appJsContent.includes('idb')) {
            report += '- [x] **IndexedDB**: Initialization found in `app.js`.\n';
        } else {
            report += '- [ ] **IndexedDB**: NOT initialized in `app.js`. Lesson content caching might be using standard cache instead of structured storage.\n';
        }
    }

    return report;
}

/**
 * Audits GitHub Actions CI/CD workflows.
 */
function auditWorkflows() {
    let report = '### CI/CD Integration Audit\n\n';
    
    if (fs.existsSync(WORKFLOWS_DIR)) {
        const files = fs.readdirSync(WORKFLOWS_DIR);
        if (files.length > 0) {
            report += `- [x] **Workflows Directory**: Found \`${WORKFLOWS_DIR}\` with ${files.length} files.\n`;
            files.forEach(file => {
                const content = fs.readFileSync(path.join(WORKFLOWS_DIR, file), 'utf8');
                if (content.includes('FirebaseExtended/action-hosting-deploy')) {
                    report += `  - [x] \`${file}\`: Configured for Firebase Hosting deployment.\n`;
                } else {
                    report += `  - [ ] \`${file}\`: Generic workflow found.\n`;
                }
            });
        } else {
            report += '- [ ] **Workflows**: Directory exists but is empty.\n';
        }
    } else {
        report += '- [ ] **Workflows Directory**: MISSING. CI/CD automation for Firebase Hosting is NOT configured.\n';
    }

    return report;
}

/**
 * Audits Firebase Hosting Status.
 */
function auditFirebaseHosting() {
    let report = '### Firebase Hosting & App Hosting Status\n\n';
    
    // Hosting Sites
    const sites = runCommand('firebase hosting:sites:list --json');
    report += `#### Active Sites\n\`\`\`json\n${sites}\n\`\`\`\n\n`;

    // Release History
    // Using default site since we found it in sites:list
    const releases = runCommand('firebase hosting:releases --json');
    report += `#### Recent Releases\n\`\`\`json\n${releases}\n\`\`\`\n\n`;

    return report;
}

/**
 * Generates the manual verification checklist for Quotas.
 */
function generateQuotasSection() {
    return `### Usage & Quotas (Spark Plan Audit)
- [ ] **Storage Space**: Verify current usage < 1GB in Firebase Console.
- [ ] **Data Transfer**: Verify monthly transfer < 10GB.
- [ ] **Custom Domains**: Check for \`congolang.cg\` or similar in Hosting settings.

> [!NOTE]
> The Spark plan is limited. If "CongoLang" scales with heavy audio assets, consider the "Blaze" (pay-as-you-go) plan.
`;
}

/**
 * Generates a suggested GitHub Actions workflow for Firebase Hosting.
 */
function generateSuggestedWorkflow() {
    return `
### [SUGGESTED] CI/CD Workflow (.github/workflows/firebase-hosting.yml)
\`\`\`yaml
name: Deploy to Firebase Hosting
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
jobs:
  build_and_deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          repoToken: '\${{ secrets.GITHUB_TOKEN }}'
          firebaseServiceAccount: '\${{ secrets.FIREBASE_SERVICE_ACCOUNT_CONGOLANG }}'
          projectId: congolang
\`\`\`
`;
}

/**
 * Main execution function.
 */
function generateReport() {
    console.log('--- Generating CongoLang Web State Report ---');
    
    let fullReport = `# CongoLang Web State Report\n`;
    fullReport += `*Generated on: ${new Date().toLocaleString()}*\n\n`;

    fullReport += auditFirebaseHosting();
    fullReport += auditPWA();
    fullReport += auditWorkflows();
    
    if (!fs.existsSync(WORKFLOWS_DIR)) {
        fullReport += generateSuggestedWorkflow();
    }

    fullReport += '\n' + generateQuotasSection();

    // Final Summary Section
    fullReport += `\n### Configuration Drift & Summary
- Local \`firebase.json\` vs Server: Manual check required via \`firebase hosting:sites:list\`.
- Preview Channels: Check "Active Channels" in Firebase Console for existing PR previews.
`;

    fs.writeFileSync(REPORT_FILE, fullReport);
    console.log(`[SUCCESS] Report generated: ${REPORT_FILE}`);
}

generateReport();
