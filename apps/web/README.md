# OCTOPUS-DT Web Dashboard

Next.js + Three.js interactive morphology preview. Deploy this directory as the Vercel project root: `apps/web`.

## Local development

    npm install
    npm run dev

## Production build

    npm run build

The browser scene is a procedural visualization only. It is not connected to the MuJoCo engine and does not represent calibrated pneumatic actuation or fluid dynamics. The MuJoCo simulator remains in the Python package under `simulation/`.
