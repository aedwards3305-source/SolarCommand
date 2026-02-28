interface PageHeroProps {
  title: string;
  subtitle?: string;
  description?: string;
}

export default function PageHero({
  title,
  subtitle,
  description,
}: PageHeroProps) {
  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-solar-600 via-solar-700 to-solar-800 text-white">
      <div className="absolute inset-0 opacity-10">
        <div className="absolute -top-40 -right-40 h-[400px] w-[400px] rounded-full bg-solar-400 blur-3xl" />
        <div className="absolute -bottom-20 -left-20 h-[250px] w-[250px] rounded-full bg-fuchsia-400 blur-3xl" />
      </div>
      <div className="relative mx-auto max-w-5xl px-4 py-16 text-center sm:px-6 sm:py-24">
        {subtitle && (
          <p className="text-lg font-medium uppercase tracking-wider text-solar-200 sm:text-xl">
            {subtitle}
          </p>
        )}
        <h1 className="mt-3 text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-7xl">
          {title}
        </h1>
        {description && (
          <p className="mx-auto mt-5 max-w-3xl text-xl text-solar-100 sm:text-2xl leading-relaxed">
            {description}
          </p>
        )}
      </div>
    </section>
  );
}
