/* UPDATE THESE VALUES TO MATCH YOUR SETUP */

const BASE_URL = window.API_BASE_URL;
const PROCESSING_STATS_API_URL = `http://${BASE_URL}/processing/stats`
const ANALYZER_API_URL = {
    stats: `http://${BASE_URL}/analyzer/stats`,
    park: (index) => `http://${BASE_URL}/analyzer/park?index=${index}`,
    reserve: (index) => `http://${BASE_URL}/analyzer/reserve?index=${index}`
}
const CONSISTENCY_CHECK_API_URL = {
    checks: `http://${BASE_URL}/consistency/checks`,
    update: `http://${BASE_URL}/consistency/update`
}

// This function fetches and updates the general statisticss
const makeReq = (url, cb, method = "GET", body = null) => {
    fetch(url, {
        method: method,  // Use the specified method (default is GET)
        headers: { "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : null  // Include body if needed
    })
    .then(res => res.json())
    .then((result) => {
        console.log("Received data: ", result);
        cb(result);
    }).catch((error) => {
        updateErrorMessages(error.message);
    });
};

const updateCodeDiv = (elemId, text) => document.getElementById(elemId).innerText = text

const getLocaleDateStr = () => (new Date()).toLocaleString()

const getStats = () => {
    document.getElementById("last-updated-value").innerText = getLocaleDateStr()
    
    makeReq(PROCESSING_STATS_API_URL, (result) => {
        updateCodeDiv("processing-stats", 
            `Number of Parked Cars: ${result.num_pc_reports}
            Number of Reserved Spots: ${result.num_sr_reports}`
        )
    })

    makeReq(ANALYZER_API_URL.stats, (statsResult) => {
        updateCodeDiv("analyzer-stats",
            `Number of Parked Cars: ${statsResult.num_park_car}
            Number of Reserved Spots: ${statsResult.num_reserve_spot}`
        )

        // get the last index for each event
        const lastParkIndex = Math.max(statsResult.num_park_car - 1, 0)
        const lastReserveIndex = Math.max(statsResult.num_reserve_spot - 1, 0)

        makeReq(ANALYZER_API_URL.park(0), (result) => {
            updateCodeDiv("first-event-park",
                `Parking duration of the first car: ${result.parking_duration}`
            )
        })
        
        makeReq(ANALYZER_API_URL.park(lastParkIndex), (result) => {
            updateCodeDiv("last-event-park",
                `Parking duration of a random car: ${result.parking_duration}`
            )
        })

        makeReq(ANALYZER_API_URL.reserve(0), (result) => {
            updateCodeDiv("first-event-reserve",
                `Parking time of the first spot reservation: ${result.parking_time}`
            )
        })

        makeReq(ANALYZER_API_URL.reserve(lastReserveIndex), (result) => {
            updateCodeDiv("last-event-reserve",
                `Parking time of a random spot reservation: ${result.parking_time}`
            )
        })
    })
}

const checkConsistency = () => {
    makeReq(CONSISTENCY_CHECK_API_URL.update, (result) => {
        updateCodeDiv("consistency-check-time", 
            `Processing time: ${result.processing_time_ms} ms`
        );

        // Now that update is done, run /checks
        makeReq(CONSISTENCY_CHECK_API_URL.checks, (result) => {
            updateCodeDiv("db-info", 
                `Number of Parked Cars: ${result.counts.db.park_car}
                Number of Reserved Spots: ${result.counts.db.reserve_spot}`
            );

            updateCodeDiv("processing-storage-info", 
                `Number of Parked Cars: ${result.counts.processing.park_car}
                Number of Reserved Spots: ${result.counts.processing.reserve_spot}`
            );

            updateCodeDiv("queue-storage-info", 
                `Number of Parked Cars: ${result.counts.queue.park_car}
                Number of Reserved Spots: ${result.counts.queue.reserve_spot}`
            );

            updateCodeDiv("missing-data-info", 
                `IDs missing in Database:\n` +
                result.missing_in_db.map(entry => 
                    `Device ID: ${entry.device_id}, Trace ID: ${entry.trace_id}, Type: ${entry.type}`
                ).join("\n") +
                `\n\nIDs missing in Queue:\n` +
                result.missing_in_queue.map(entry => 
                    `Device ID: ${entry.device_id}, Trace ID: ${entry.trace_id}, Type: ${entry.type}`
                ).join("\n")
            );            

            updateCodeDiv("consistency-check-update", 
                `Last Updated: ${result.last_updated}`
            );
        });
    }, "POST");
};




const updateErrorMessages = (message) => {
    const id = Date.now()
    console.log("Creation", id)
    msg = document.createElement("div")
    msg.id = `error-${id}`
    msg.innerHTML = `<p>Something happened at ${getLocaleDateStr()}!</p><code>${message}</code>`
    document.getElementById("messages").style.display = "block"
    document.getElementById("messages").prepend(msg)
    setTimeout(() => {
        const elem = document.getElementById(`error-${id}`)
        if (elem) { elem.remove() }
    }, 7000)
}

const setup = () => {
    getStats()
    setInterval(() => getStats(), 4000) // Update every 4 seconds
    document.getElementById("consistency-btn").addEventListener("click", checkConsistency)
}

document.addEventListener('DOMContentLoaded', setup)