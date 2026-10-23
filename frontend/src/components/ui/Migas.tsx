import Link from "next/link";
import Icono from "./Icono";

export interface Miga {
  texto: string;
  /** Sin `href` = página actual. */
  href?: string;
}

/** Migas de pan: orientan en páginas profundas. La última es la página actual (aria-current). */
export default function Migas({ items }: { items: Miga[] }) {
  return (
    <nav aria-label="Migas de pan" className="mb-3">
      <ol className="flex flex-wrap items-center gap-x-1.5 gap-y-1 text-sm text-suave">
        {items.map((m, i) => {
          const ultima = i === items.length - 1;
          return (
            <li key={`${m.texto}-${i}`} className="flex min-w-0 items-center gap-1.5">
              {i > 0 && <Icono nombre="chevron" tamano={14} className="-rotate-90 shrink-0 opacity-60" />}
              {m.href && !ultima ? (
                <Link href={m.href} className="inline-flex min-h-8 items-center rounded font-semibold text-enlace hover:underline">
                  {m.texto}
                </Link>
              ) : (
                <span aria-current={ultima ? "page" : undefined} className="max-w-[16rem] truncate font-semibold text-texto sm:max-w-md">
                  {m.texto}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
