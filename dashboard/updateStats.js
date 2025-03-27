/* UPDATE THESE VALUES TO MATCH YOUR SETUP */

const BASE_URL = window.API_BASE_URL;
const PROCESSING_STATS_API_URL = `http://${BASE_URL}:8100/stats`
const ANALYZER_API_URL = {
    stats: `http://${BASE_URL}:8110/stats`,
    park: (index) => `http://${BASE_URL}:8110/park?index=${index}`,
    reserve: (index) => `http://${BASE_URL}:8110/reserve?index=${index}`
}

// This function fetches and updates the general statistics
const makeReq = (url, cb) => {
    fetch(url)
        .then(res => res.json())
        .then((result) => {
            console.log("Received data: ", result)
            cb(result);
        }).catch((error) => {
            updateErrorMessages(error.message)
        })
}

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
        updateCodeDiv("analyzer-stats", statsResult)

        // get the last index for each events
        const lastParkIndex = Math.max(statsResult.num_park_car - 1, 0)
        const lastReserveIndex = Math.max(statsResult.num_reserve_car - 1, 0)
        // const randomParkIndex = Math.floor(Math.random() * (Math.max(statsResult.num_park_car - 1, 0)))
        // const randomReserveIndex = Math.floor(Math.random() * (Math.max(statsResult.num_reserve_car - 1, 0)))

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
}

document.addEventListener('DOMContentLoaded', setup)