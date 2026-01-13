"use client";

import React from 'react';

const DataDiggingLoader = () => {
    return (
        <div className="flex flex-col items-center justify-center p-8">
            <div className="drill-loader relative w-[60px] h-[100px]">
                <style jsx>{`
          /* Urbja konteiners */
          .drill-loader {
            position: relative;
            width: 60px;
            height: 100px;
          }

          /* Pats urbis (trīsstūris) */
          .drill-bit {
            width: 0;
            height: 0;
            border-left: 15px solid transparent;
            border-right: 15px solid transparent;
            border-top: 30px solid #6366f1; /* Indigo krāsa */
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            /* Animācija: griežas un kustas uz leju/augšu */
            animation: drillDown 2s cubic-bezier(0.65, 0, 0.35, 1) infinite;
            z-index: 2;
          }
          
          /* Datu slāņi, caur kuriem urbj */
          .data-layer {
            width: 60px;
            height: 12px;
            background-color: #1e293b;
            border-radius: 4px;
            margin-bottom: 6px;
            position: absolute;
            left: 0;
            /* Animācija: saraujas, kad urbis pieskaras */
            animation: layerCrunch 2s cubic-bezier(0.65, 0, 0.35, 1) infinite;
          }

          /* Pozicionējam slāņus un iestatām aizturi */
          .layer-1 { top: 40px; animation-delay: 0.2s; }
          .layer-2 { top: 60px; animation-delay: 0.4s; }
          .layer-3 { top: 80px; animation-delay: 0.6s; }

          /* Datu daļiņas, kas izlido */
          .particle {
            position: absolute;
            width: 6px;
            height: 6px;
            background-color: #f59e0b; /* Dzeltens/Zelts - izraktais dati */
            border-radius: 50%;
            opacity: 0;
            z-index: 1;
            animation: particleUp 2s ease-out infinite;
          }
          .p1 { left: 10px; animation-delay: 0.3s; }
          .p2 { right: 10px; animation-delay: 0.5s; }
          .p3 { left: 50%; animation-delay: 0.7s; }

          /* --- ANIMĀCIJAS KEYFRAMES --- */

          @keyframes drillDown {
            0% { top: 0; transform: translateX(-50%) rotate(0deg); }
            40% { top: 75px; transform: translateX(-50%) rotate(720deg); } /* Urbjas iekšā */
            60% { top: 75px; transform: translateX(-50%) rotate(720deg); } /* Neliela pauze lejā */
            100% { top: 0; transform: translateX(-50%) rotate(0deg); } /* Atgriežas augšā */
          }

          @keyframes layerCrunch {
            0%, 100% { width: 60px; transform: scaleX(1); opacity: 1; }
            30%, 50% { width: 20px; transform: scaleX(0.8); opacity: 0.5; background-color: #6366f1; } /* Slānis saraujas un iekrāsojas */
          }

          @keyframes particleUp {
            0% { opacity: 0; top: 80px; transform: scale(0.5); }
            40% { opacity: 1; top: 60px; transform: scale(1); }
            100% { opacity: 0; top: 0px; transform: scale(0.5); }
          }
        `}</style>

                <div className="drill-bit"></div>
                <div className="data-layer layer-1"></div>
                <div className="data-layer layer-2"></div>
                <div className="data-layer layer-3"></div>
                <div className="particle p1"></div>
                <div className="particle p2"></div>
                <div className="particle p3"></div>
            </div>

            <p className="mt-8 text-slate-600 font-medium animate-pulse">
                Iegūstam datus...
            </p>
        </div>
    );
};

export default DataDiggingLoader;
