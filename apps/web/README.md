# OCTOPUS-DT Web Dashboard

This directory is reserved for the Next.js + Three.js dashboard deployed on Vercel.

The dashboard will render exported simulation states, experiment metadata, plots, and validation status. Keep the MuJoCo runtime in the Python simulation environment or a separate service; Vercel should serve the frontend and lightweight APIs, not a long-running native simulation process.
