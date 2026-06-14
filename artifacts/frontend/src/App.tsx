import { Route, Switch } from "wouter";
import Layout from "./components/Layout";
import DashboardPage from "./pages/DashboardPage";
import VisionPage from "./pages/VisionPage";
import OcrPage from "./pages/OcrPage";
import AssistantPage from "./pages/AssistantPage";

export default function App() {
  return (
    <Layout>
      <Switch>
        <Route path="/" component={DashboardPage} />
        <Route path="/dashboard" component={DashboardPage} />
        <Route path="/vision" component={VisionPage} />
        <Route path="/ocr" component={OcrPage} />
        <Route path="/assistant" component={AssistantPage} />
        <Route>
          <div className="loading-state">
            <p className="text-muted">Page not found</p>
          </div>
        </Route>
      </Switch>
    </Layout>
  );
}
