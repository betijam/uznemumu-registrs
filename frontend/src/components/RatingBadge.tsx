import React from 'react';

export const RatingBadge = ({ grade }: { grade: string }) => {
    let colorClass = "bg-gray-100 text-gray-800";
    if (["A", "A+", "A-"].includes(grade)) colorClass = "bg-green-100 text-green-800";
    else if (["B", "B+", "B-"].includes(grade)) colorClass = "bg-blue-100 text-blue-800";
    else if (["C", "C+", "C-"].includes(grade)) colorClass = "bg-yellow-100 text-yellow-800";
    else if (["D", "E", "F"].includes(grade)) colorClass = "bg-red-100 text-red-800";

    return (
        <span className={`px-2 py-1 rounded text-xs font-semibold ${colorClass}`}>
            {grade}
        </span>
    );
};
