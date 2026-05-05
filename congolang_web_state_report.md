# CongoLang Web State Report
*Generated on: 4. 5. 2026 15:33:25*

### Firebase Hosting & App Hosting Status

#### Active Sites
```json
{
  "status": "success",
  "result": {
    "sites": [
      {
        "name": "projects/congolang/sites/congolang",
        "defaultUrl": "https://congolang.web.app",
        "appId": "1:823661895203:web:f76c740256df60bbe45b96",
        "type": "DEFAULT_SITE"
      }
    ]
  }
}
```

#### Recent Releases
```json
[ERROR] Failed to execute: firebase hosting:releases --json
Command failed: firebase hosting:releases --json --non-interactive
```

### PWA & Offline Readiness

- [x] **Service Worker**: Found at `public\service-worker.js`.
  - [x] Static assets caching implemented.
- [x] **Manifest**: Found at `public\manifest.json`.
- [ ] **IndexedDB**: NOT initialized in `app.js`. Lesson content caching might be using standard cache instead of structured storage.
### CI/CD Integration Audit

- [ ] **Workflows Directory**: MISSING. CI/CD automation for Firebase Hosting is NOT configured.

### [SUGGESTED] CI/CD Workflow (.github/workflows/firebase-hosting.yml)
```yaml
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
          repoToken: '${{ secrets.GITHUB_TOKEN }}'
          firebaseServiceAccount: '${{ secrets.FIREBASE_SERVICE_ACCOUNT_CONGOLANG }}'
          projectId: congolang
```

### Usage & Quotas (Spark Plan Audit)
- [ ] **Storage Space**: Verify current usage < 1GB in Firebase Console.
- [ ] **Data Transfer**: Verify monthly transfer < 10GB.
- [ ] **Custom Domains**: Check for `congolang.cg` or similar in Hosting settings.

> [!NOTE]
> The Spark plan is limited. If "CongoLang" scales with heavy audio assets, consider the "Blaze" (pay-as-you-go) plan.

### Configuration Drift & Summary
- Local `firebase.json` vs Server: Manual check required via `firebase hosting:sites:list`.
- Preview Channels: Check "Active Channels" in Firebase Console for existing PR previews.
