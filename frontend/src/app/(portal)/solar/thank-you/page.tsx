export default function ThankYouPage() {
  return (
    <div className="mx-auto max-w-xl px-4 py-20 text-center">
      <div className="rounded-2xl bg-white p-8 shadow-sm border border-gray-200 sm:p-10">
        {/* Checkmark */}
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
          <svg
            width={32}
            height={32}
            className="h-8 w-8 text-green-600"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M4.5 12.75l6 6 9-13.5"
            />
          </svg>
        </div>

        <h1 className="mt-5 text-2xl font-bold text-gray-900">
          Thank You!
        </h1>
        <p className="mt-2 text-gray-600">
          Your free solar quote request has been received. Our team will be in
          touch shortly.
        </p>

        <div className="mt-6 rounded-xl bg-solar-50 p-4">
          <p className="text-sm font-medium text-solar-800">
            Check your text messages
          </p>
          <p className="mt-1 text-xs text-solar-600">
            We&apos;ll send you a link to your personalized solar portal where you
            can view your estimated savings and schedule a consultation.
          </p>
        </div>

        <div className="mt-8 space-y-3">
          <a
            href="/solar/get-quote"
            className="block w-full rounded-lg bg-solar-600 px-6 py-3 text-sm font-bold text-white hover:bg-solar-700 transition-colors"
          >
            Get Another Quote
          </a>
          <a
            href="/solar"
            className="block w-full text-center text-sm text-gray-500 hover:text-solar-600 transition-colors py-1"
          >
            Back to Home
          </a>
        </div>
      </div>
    </div>
  );
}
