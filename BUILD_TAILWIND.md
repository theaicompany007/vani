# Building Tailwind CSS

This project uses Tailwind CSS compiled from source files instead of the CDN to avoid production warnings.

## Setup

1. **Install Node.js** (if not already installed)
   - Download from https://nodejs.org/
   - Verify installation: `node --version` and `npm --version`

2. **Install dependencies**
   ```bash
   npm install
   ```

## Building CSS

### One-time build (for production)
```bash
npm run build-css
```

This will:
- Read `app/static/css/input.css`
- Process it with Tailwind CSS
- Output minified CSS to `app/static/css/tailwind.css`

### Watch mode (for development)
```bash
npm run watch-css
```

This will automatically rebuild the CSS whenever you make changes to your HTML templates or input CSS file.

## Files

- `tailwind.config.js` - Tailwind configuration
- `app/static/css/input.css` - Source CSS file with Tailwind directives
- `app/static/css/tailwind.css` - Compiled CSS (generated, don't edit directly)
- `package.json` - Node.js dependencies and scripts

## Notes

- The compiled CSS file (`tailwind.css`) should be committed to version control
- Run `npm run build-css` before deploying to production
- The HTML template uses `url_for('static', filename='css/tailwind.css')` to load the compiled CSS

















