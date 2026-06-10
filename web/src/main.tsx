import { createRoot } from "react-dom/client"

import App from "./App"
import { connectToAnki } from "./sse"

connectToAnki()
createRoot(document.getElementById("root")!).render(<App />)
