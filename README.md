<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/drive/1MoVAPk6BDgtcZMl1E2jJlcQEx-VCgcMx

## Run Locally

**Prerequisites:**  Node.js

1. Install dependencies:
   ```bash
   npm install
   ```
2. Set the `GEMINI_API_KEY` in `.env.local` to your Gemini API key (optional for AI features).
3. **Intro video:** Keep `WonderNest.mp4` in the project root. When you run `npm run dev`, it is copied to `public/` and used as the welcome intro (with a Skip button).
4. Run the app:
   ```bash
   npm run dev
   ```
   Then open **http://localhost:3000** in your browser.
