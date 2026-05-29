import { Navbar } from "../components/marketing/Navbar";
import { Hero } from "../components/marketing/Hero";
import { ProblemSection } from "../components/marketing/ProblemSection";
import { Features } from "../components/marketing/Features";
import { HowItWorks } from "../components/marketing/HowItWorks";
import { TrustSection } from "../components/marketing/TrustSection";
import { Pricing } from "../components/marketing/Pricing";
import { FAQ } from "../components/marketing/FAQ";
import { CTASection } from "../components/marketing/CTASection";
import { Footer } from "../components/marketing/Footer";

export default function Landing() {
  return (
    <div className="min-h-screen bg-paper">
      <Navbar />
      <main>
        <Hero />
        <ProblemSection />
        <Features />
        <HowItWorks />
        <TrustSection />
        <Pricing />
        <FAQ />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}
