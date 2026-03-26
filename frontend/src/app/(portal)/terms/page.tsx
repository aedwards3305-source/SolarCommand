import type { Metadata } from "next";
import Link from "next/link";
import PageHero from "@/components/portal/PageHero";

export const metadata: Metadata = {
  title: "Terms & Conditions | Solar Command",
  description:
    "Solar Command terms and conditions of use. Read our terms of service before using our website or services. MHIC #165263.",
};

export default function TermsPage() {
  return (
    <div>
      <PageHero
        title="Terms & Conditions"
        subtitle="Terms of Use"
        description="Please read these terms and conditions carefully before using our website or services."
      />

      <section className="py-16 sm:py-20">
        <div className="mx-auto max-w-3xl px-4 sm:px-6">
          <p className="text-sm text-gray-500">
            Effective Date: March 26, 2026
          </p>

          {/* Introduction */}
          <div className="mt-8">
            <p className="text-base text-solar-700 leading-relaxed">
              Welcome to the Solar Command website. These Terms &amp; Conditions
              (&quot;Terms&quot;) govern your access to and use of the Solar
              Command website, services, and any related communications. By
              accessing or using our website or services, you agree to be bound
              by these Terms. If you do not agree, please do not use our website
              or services.
            </p>
            <p className="mt-3 text-base text-solar-700 leading-relaxed">
              Solar Command (&quot;we,&quot; &quot;us,&quot; or &quot;our&quot;)
              is an authorized Sunburst Solar dealer, sponsored by Sunrun,
              serving homeowners in Maryland. We are licensed by the Maryland
              Home Improvement Commission (MHIC #165263).
            </p>
          </div>

          {/* 1. Services Overview */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              1. Services Overview
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              Solar Command provides residential solar energy consultation,
              system design, installation coordination, battery storage
              solutions, and related services. Our website allows you to:
            </p>
            <ul className="mt-3 list-disc pl-5 space-y-2 text-base text-solar-700 leading-relaxed">
              <li>
                Request free solar quotes and energy assessments.
              </li>
              <li>
                Learn about solar energy, financing options, and available
                incentives.
              </li>
              <li>
                Schedule consultations and appointments with our team.
              </li>
              <li>
                Access your personalized customer portal and project updates.
              </li>
            </ul>
            <p className="mt-3 text-base text-solar-700 leading-relaxed">
              All solar installations are performed by factory-trained, licensed,
              bonded, and insured installers. System specifications, savings
              estimates, and timelines provided on our website or in proposals
              are estimates and may vary based on your specific property and
              circumstances.
            </p>
          </div>

          {/* 2. Eligibility */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              2. Eligibility
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              You must be at least 18 years of age and a homeowner or authorized
              representative of a property owner to request a quote or enter
              into a service agreement with Solar Command. By using our
              services, you represent that you meet these requirements.
            </p>
          </div>

          {/* 3. Quotes & Proposals */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              3. Quotes &amp; Proposals
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              Solar quotes and proposals provided by Solar Command are estimates
              based on information available at the time of preparation,
              including satellite imagery, utility data, and information you
              provide. Actual system performance, savings, and costs may differ
              from estimates due to factors including but not limited to:
            </p>
            <ul className="mt-3 list-disc pl-5 space-y-2 text-base text-solar-700 leading-relaxed">
              <li>
                Changes in your energy consumption or utility rates.
              </li>
              <li>
                Site conditions discovered during the installation process.
              </li>
              <li>
                Changes in applicable tax credits, rebates, or incentive
                programs.
              </li>
              <li>
                Equipment availability and pricing changes.
              </li>
            </ul>
            <p className="mt-3 text-base text-solar-700 leading-relaxed">
              Quotes are valid for the period stated in the proposal. A quote
              does not constitute a binding contract until a separate
              installation agreement is signed by both parties.
            </p>
          </div>

          {/* 4. Financing */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              4. Financing
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              Solar Command may offer financing options through third-party
              lending partners. Financing terms, interest rates, and approval
              are determined by the financing provider and are subject to credit
              approval. Solar Command is not a lender and does not guarantee
              financing approval or specific terms.
            </p>
            <p className="mt-3 text-base text-solar-700 leading-relaxed">
              You are responsible for reviewing and understanding all financing
              terms before entering into any financing agreement. Questions
              about financing terms should be directed to the financing
              provider.
            </p>
          </div>

          {/* 5. Warranties & Guarantees */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              5. Warranties &amp; Guarantees
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              Solar Command installations include manufacturer warranties and a
              comprehensive 25-year warranty with production guarantee, as
              provided through Sunburst Solar and Sunrun. Specific warranty
              terms and conditions are detailed in your installation agreement
              and warranty documentation.
            </p>
            <p className="mt-3 text-base text-solar-700 leading-relaxed">
              Warranty coverage is subject to the terms set by the equipment
              manufacturer and Sunrun. Solar Command will assist you in
              processing any warranty claims, but ultimate warranty obligations
              rest with the applicable manufacturer or warranty provider.
            </p>
          </div>

          {/* 6. Website Use */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              6. Website Use
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              When using our website, you agree not to:
            </p>
            <ul className="mt-3 list-disc pl-5 space-y-2 text-base text-solar-700 leading-relaxed">
              <li>
                Use the website for any unlawful purpose or in violation of
                these Terms.
              </li>
              <li>
                Provide false, misleading, or inaccurate information when
                submitting forms or communicating with us.
              </li>
              <li>
                Attempt to gain unauthorized access to any portion of the
                website, server, or connected systems.
              </li>
              <li>
                Interfere with or disrupt the website or its infrastructure.
              </li>
              <li>
                Scrape, harvest, or collect information from the website using
                automated means without our written consent.
              </li>
              <li>
                Reproduce, distribute, or create derivative works from website
                content without our prior written permission.
              </li>
            </ul>
          </div>

          {/* 7. Intellectual Property */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              7. Intellectual Property
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              All content on this website &mdash; including text, graphics,
              logos, images, and software &mdash; is the property of Solar
              Command or its licensors and is protected by applicable
              intellectual property laws. You may not use, copy, or distribute
              any content from this website without our prior written consent.
            </p>
            <p className="mt-3 text-base text-solar-700 leading-relaxed">
              The Solar Command name, logo, and all related trademarks are the
              property of Solar Command. Sunburst Solar, Sunrun, and Enphase are
              trademarks of their respective owners.
            </p>
          </div>

          {/* 8. Communications & Text Messages */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              8. Communications &amp; Text Messages
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              By submitting your contact information through our website or
              requesting a quote, you consent to receive communications from
              Solar Command, including phone calls, emails, and SMS text
              messages related to your inquiry and our services.
            </p>
            <p className="mt-3 text-base text-solar-700 leading-relaxed">
              For SMS messages: message and data rates may apply. Message
              frequency varies. You may opt out at any time by replying
              &quot;STOP&quot; to any text message. Reply &quot;HELP&quot; for
              assistance. See our{" "}
              <Link
                href="/privacy-policy"
                className="font-medium text-solar-600 hover:text-solar-700 underline underline-offset-2"
              >
                Privacy Policy
              </Link>{" "}
              for more details on how we handle your information.
            </p>
          </div>

          {/* 9. Limitation of Liability */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              9. Limitation of Liability
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              To the fullest extent permitted by Maryland law, Solar Command
              shall not be liable for any indirect, incidental, special,
              consequential, or punitive damages arising out of or related to
              your use of our website or services, including but not limited to
              loss of profits, data, or other intangible losses.
            </p>
            <p className="mt-3 text-base text-solar-700 leading-relaxed">
              Our total liability for any claim arising under these Terms shall
              not exceed the amount you have paid to Solar Command for the
              specific service giving rise to the claim. Nothing in these Terms
              excludes or limits liability that cannot be excluded or limited
              under applicable law.
            </p>
          </div>

          {/* 10. Disclaimer of Warranties */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              10. Disclaimer of Warranties
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              The website and its content are provided &quot;as is&quot; and
              &quot;as available&quot; without warranties of any kind, either
              express or implied, including but not limited to implied warranties
              of merchantability, fitness for a particular purpose, or
              non-infringement.
            </p>
            <p className="mt-3 text-base text-solar-700 leading-relaxed">
              We do not warrant that the website will be uninterrupted,
              error-free, or free of harmful components. Savings estimates,
              energy production projections, and financial calculations presented
              on our website are for informational purposes only and do not
              constitute guarantees.
            </p>
          </div>

          {/* 11. Indemnification */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              11. Indemnification
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              You agree to indemnify, defend, and hold harmless Solar Command,
              its officers, directors, employees, and agents from any claims,
              liabilities, damages, losses, or expenses (including reasonable
              attorneys&apos; fees) arising out of your use of our website or
              services, your violation of these Terms, or your violation of any
              rights of a third party.
            </p>
          </div>

          {/* 12. Governing Law */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              12. Governing Law &amp; Dispute Resolution
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              These Terms are governed by and construed in accordance with the
              laws of the State of Maryland, without regard to its conflict of
              law provisions. Any disputes arising under these Terms shall be
              resolved in the state or federal courts located in Maryland, and
              you consent to the personal jurisdiction of such courts.
            </p>
            <p className="mt-3 text-base text-solar-700 leading-relaxed">
              Before filing any formal legal proceeding, you agree to first
              contact Solar Command to attempt to resolve the dispute informally.
              We will make reasonable efforts to resolve any concerns promptly
              and in good faith.
            </p>
          </div>

          {/* 13. Changes to These Terms */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              13. Changes to These Terms
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              We may update these Terms from time to time. When we do, we will
              revise the &quot;Effective Date&quot; at the top of this page.
              Your continued use of our website or services after any changes
              constitutes your acceptance of the updated Terms. We encourage you
              to review these Terms periodically.
            </p>
          </div>

          {/* 14. Severability */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              14. Severability
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              If any provision of these Terms is found to be invalid or
              unenforceable, the remaining provisions shall continue in full
              force and effect. The invalid or unenforceable provision shall be
              modified to the minimum extent necessary to make it valid and
              enforceable.
            </p>
          </div>

          {/* 15. Contact Us */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              15. Contact Us
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              If you have questions about these Terms &amp; Conditions, please
              contact us:
            </p>
            <div className="mt-4 rounded-xl bg-white p-6 shadow-sm border border-gray-200">
              <p className="text-base font-semibold text-solar-700">
                Solar Command
              </p>
              <p className="mt-1 text-base text-solar-700">
                8115 Maplelawn Blvd, Fulton, MD
              </p>
              <p className="mt-1 text-base text-solar-700">
                Available Mon&ndash;Sat, 8am&ndash;6pm
              </p>
              <p className="mt-3 text-base text-solar-700">
                <Link
                  href="/get-quote"
                  className="font-medium text-solar-600 hover:text-solar-700 underline underline-offset-2"
                >
                  Contact Us via Quote Form
                </Link>
              </p>
            </div>
          </div>

          {/* Maryland Disclosure */}
          <div className="mt-12 rounded-xl bg-gray-50 p-6 border border-gray-200">
            <p className="text-sm text-gray-500 leading-relaxed">
              Solar Command is licensed by the Maryland Home Improvement
              Commission (MHIC #165263). We are an authorized Sunburst Solar
              dealer, sponsored by Sunrun. These Terms &amp; Conditions were
              last updated on March 26, 2026.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
