// Uso: node grabar.js [escena ...]   (sin argumentos graba todas, en orden)
const { ESCENAS } = require("./escenas");
const { cerrarNavegador } = require("./lib");

(async () => {
  const pedidas = process.argv.slice(2);
  const nombres = pedidas.length ? pedidas : Object.keys(ESCENAS);
  try {
    for (const n of nombres) {
      if (!ESCENAS[n]) throw new Error("Escena desconocida: " + n);
      await ESCENAS[n]();
    }
  } finally {
    await cerrarNavegador();
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
