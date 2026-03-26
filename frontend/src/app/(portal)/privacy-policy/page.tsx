import type { Metadata } from "next";
import Link from "next/link";
import PageHero from "@/components/portal/PageHero";

export const metadata: Metadata = {
  title: "Privacy Policy | Solar Command",
  description:
    "Solar Command privacy policy. Learn how we collect, use, and protect your personal information. MHIC #165263.",
};

export default function PrivacyPolicyPage() {
  return (
    <div>
      <PageHero
        title="Privacy Policy"
        subtitle="Your Privacy Matters"
        description="This policy describes how Solar Command collects, uses, and protects your personal information."
      />

      <section className="py-16 sm:py-20">
        <div className="mx-auto max-w-3xl px-4 sm:px-6">
          <p className="text-sm text-gray-500">
            Effective Date: March 26, 2026
          </p>

          {/* Introduction */}
          <div className="mt-8">
            <p className="text-base text-solar-700 leading-relaxed">
              Solar Command (&quot;we,&quot; &quot;us,&quot; or &quot;our&quot;)
              is an authorized Sunburst Solar dealer, sponsored by Sunrun,
              serving homeowners in Maryland. We are committed to protecting your
              privacy. This Privacy Policy explains what information we collect,
              how we use it, and the choices you have.
            </p>
          </div>

          {/* 1. Information We Collect */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              1. Information We Collect
            </h2>

            <h3 className="mt-6 text-lg font-semibold text-solar-700">
              Information You Provide
            </h3>
            <ul className="mt-2 list-disc pl-5 space-y-2 text-base text-solar-700 leading-relaxed">
              <li>
                <strong>Contact details</strong> &mdash; name, email address,
                phone number, and home address submitted through our quote
                request forms.
              </li>
              <li>
                <strong>Property information</strong> &mdash; details about your
                roof, electricity usage, and utility bills that help us design
                your solar system.
              </li>
              <li>
                <strong>Communications</strong> &mdash; messages, emails, and
                text messages you exchange with our team.
              </li>
            </ul>

            <h3 className="mt-6 text-lg font-semibold text-solar-700">
              Information Collected Automatically
            </h3>
            <ul className="mt-2 list-disc pl-5 space-y-2 text-base text-solar-700 leading-relaxed">
              <li>
                <strong>Device &amp; browser data</strong> &mdash; IP address,
                browser type, operating system, and device identifiers.
              </li>
              <li>
                <strong>Usage data</strong> &mdash; pages visited, time spent on
                pages, and referring URLs.
              </li>
              <li>
                <strong>Cookies &amp; similar technologies</strong> &mdash; we
                use cookies to improve site functionality and analyze traffic.
                See Section 5 for details.
              </li>
            </ul>
          </div>

          {/* 2. How We Use Your Information */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              2. How We Use Your Information
            </h2>
            <ul className="mt-4 list-disc pl-5 space-y-2 text-base text-solar-700 leading-relaxed">
              <li>
                Prepare and deliver your custom solar proposal, including
                satellite imagery analysis and system design.
              </li>
              <li>
                Communicate with you about your quote, appointment scheduling,
                installation status, and post-installation support.
              </li>
              <li>
                Send SMS text messages related to your inquiry or service (see
                Section 6 for details on text messaging).
              </li>
              <li>
                Process permits, utility interconnection paperwork, and
                financing applications on your behalf.
              </li>
              <li>
                Improve our website, services, and customer experience.
              </li>
              <li>
                Comply with legal obligations and protect our rights.
              </li>
            </ul>
          </div>

          {/* 3. Information Sharing */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              3. Information Sharing
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              We do not sell your personal information. We may share information
              with the following parties as necessary to provide our services:
            </p>
            <ul className="mt-4 list-disc pl-5 space-y-2 text-base text-solar-700 leading-relaxed">
              <li>
                <strong>Sunrun / Sunburst Solar</strong> &mdash; as our
                sponsoring manufacturer and warranty provider, they receive
                information needed to process your installation, warranty, and
                production guarantee.
              </li>
              <li>
                <strong>Financing partners</strong> &mdash; if you choose a
                financing option, we share information required to process your
                application.
              </li>
              <li>
                <strong>Utility companies &amp; local authorities</strong>{" "}
                &mdash; to handle permitting, interconnection, and net metering
                enrollment.
              </li>
              <li>
                <strong>Service providers</strong> &mdash; third-party tools
                that help us operate our website, send communications, and
                manage customer relationships. These providers are bound by
                contract to use your data only for the services they provide to
                us.
              </li>
              <li>
                <strong>Legal compliance</strong> &mdash; when required by law,
                court order, or to protect the safety and rights of Solar
                Command, our customers, or the public.
              </li>
            </ul>
          </div>

          {/* 4. Data Security */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              4. Data Security
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              We implement reasonable technical and organizational safeguards to
              protect your personal information from unauthorized access, loss,
              or misuse. These include encrypted data transmission (TLS),
              secure server infrastructure, and access controls limiting
              employee access to personal data on a need-to-know basis.
            </p>
            <p className="mt-3 text-base text-solar-700 leading-relaxed">
              No method of transmission over the Internet or electronic storage
              is 100% secure. While we strive to protect your data, we cannot
              guarantee absolute security.
            </p>
          </div>

          {/* 5. Cookies */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              5. Cookies &amp; Tracking Technologies
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              Our website uses cookies and similar technologies to:
            </p>
            <ul className="mt-3 list-disc pl-5 space-y-2 text-base text-solar-700 leading-relaxed">
              <li>Remember your preferences and session information.</li>
              <li>Analyze site traffic and usage patterns.</li>
              <li>
                Measure the effectiveness of our marketing campaigns.
              </li>
            </ul>
            <p className="mt-3 text-base text-solar-700 leading-relaxed">
              You can control cookies through your browser settings. Disabling
              cookies may affect certain site functionality.
            </p>
          </div>

          {/* 6. Text Messaging */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              6. Text Messaging (SMS)
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              By providing your phone number and requesting a quote or
              contacting us, you consent to receive text messages from Solar
              Command related to your inquiry, appointment, and service updates.
              Message and data rates may apply. Message frequency varies.
            </p>
            <p className="mt-3 text-base text-solar-700 leading-relaxed">
              You may opt out of text messages at any time by replying
              &quot;STOP&quot; to any message. Reply &quot;HELP&quot; for
              assistance. Opting out of texts will not affect your ability to
              receive service from us.
            </p>
          </div>

          {/* 7. Your Rights */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              7. Your Rights &amp; Choices
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              You have the right to:
            </p>
            <ul className="mt-3 list-disc pl-5 space-y-2 text-base text-solar-700 leading-relaxed">
              <li>
                Request access to the personal information we hold about you.
              </li>
              <li>
                Request correction of inaccurate or incomplete information.
              </li>
              <li>
                Request deletion of your personal information, subject to our
                legal and contractual obligations.
              </li>
              <li>
                Opt out of marketing communications at any time.
              </li>
            </ul>
            <p className="mt-3 text-base text-solar-700 leading-relaxed">
              To exercise any of these rights, please contact us using the
              information below.
            </p>
          </div>

          {/* 8. Third-Party Links */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              8. Third-Party Links
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              Our website may contain links to third-party websites. We are not
              responsible for the privacy practices or content of those sites.
              We encourage you to review the privacy policies of any
              third-party sites you visit.
            </p>
          </div>

          {/* 9. Children's Privacy */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              9. Children&apos;s Privacy
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              Our services are not directed to individuals under the age of 18.
              We do not knowingly collect personal information from children. If
              you believe we have collected information from a child, please
              contact us so we can promptly delete it.
            </p>
          </div>

          {/* 10. Changes to This Policy */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              10. Changes to This Policy
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              We may update this Privacy Policy from time to time. When we do,
              we will revise the &quot;Effective Date&quot; at the top of this
              page. We encourage you to review this policy periodically to stay
              informed about how we protect your information.
            </p>
          </div>

          {/* 11. Contact Us */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-amber-600">
              11. Contact Us
            </h2>
            <p className="mt-4 text-base text-solar-700 leading-relaxed">
              If you have questions or concerns about this Privacy Policy or
              your personal information, please contact us:
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
              dealer, sponsored by Sunrun.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
