# GoalMap AI

GoalMap AI is an intelligent application designed to help users discover, visualize, and achieve their goals using the power of Google's Gemini AI. It combines interactive roadmaps with AI-driven consultancy to guide users from vague aspirations to concrete execution plans.

## 🌟 Key Features

-   **AI-Powered Discovery**: Utilize Gemini AI to explore your interests and define clear, actionable goals.
-   **Interactive Roadmaps**: Visualize your journey with dynamic node-based roadmaps powered by React Flow.
-   **Smart Consultants**: Get personalized advice from specialized AI personas (e.g., career coach, fitness expert).
-   **Blueprint Generation**: Automatically generate detailed step-by-step blueprints for achieving your selected goals.
-   **Readiness Scoring**: Track your preparedness and progress with intuitive visual gauges.

## 🛠️ Tech Stack

-   **Frontend**: React 19, Vite, TypeScript
-   **State Management**: Zustand
-   **Visualization**: React Flow
-   **AI Integration**: Google Generative AI (Gemini) SDK
-   **Styling**: CSS Modules / Vanilla CSS (with Lucide React icons)
-   **Quality Control**: Biome (Linting & Formatting)

## 🚀 Getting Started

### Prerequisites

-   Node.js (v18 or higher recommended)
-   npm or yarn
-   A generic Google Gemini API Key

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/goalmap-ai.git
    cd goalmap-ai
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

3.  Set up environment variables:
    Create a `.env.local` file in the root directory and add your Gemini API key:
    ```env
    VITE_GEMINI_API_KEY=your_api_key_here
    ```

4.  Run the development server:
    ```bash
    npm run dev
    ```

    The application will be available at `http://localhost:5173`.

## 📁 Project Structure

```
src/
├── app/              # Main app layout and routing
├── components/       # Shared UI components
├── features/         # Feature-based modules
│   ├── discovery/    # Goal discovery & chat interface
│   └── visualization/# Roadmap visualization
├── services/         # External services (Gemini API)
├── stores/           # Global state management (Zustand)
└── types/            # TypeScript type definitions
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.
