function get_stream_data() {
  fetch(window.location.href+"db/stream", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    }
  }).then((response) => {
    return response.json()
  }).then(data => {
    dom_stream_list(data);
  }).then(() => {
    document.getElementById("stream-list").firstChild.firstChild.click()
  });
};

function get_clip_data(stream_id) {
  fetch(window.location.href+"db/stream/"+stream_id, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    }
  }).then((response) => {
    return response.json()
  }).then(data => {
    dom_clip_list(data);
  });
}

function get_config_data() {
  fetch(window.location.href+"conf", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    }
  }).then((response) => {
    if (!response.ok) {
      alert(response.detail)
    } else{
      return response.json()
    }
  }).then(data => {
    dom_form(data);
  })
}

function get_video_data(stream_id, start_time, end_time) {
  const url=window.location.href+"video";
  let start = [Math.floor(start_time / 3600).toString(), Math.floor((start_time % 3600) / 60).toString(), (start_time % 60).toString()]
  let end = [Math.floor(end_time / 3600).toString(), Math.floor((end_time % 3600) / 60).toString(), (end_time % 60).toString()]
  let range = "times="+start[0]+":"+start[1]+":"+start[2]+"-"+end[0]+":"+end[1]+":"+end[2]
  fetch(url, {
    method: "GET",
    headers: {
      "Content-Type": "video/mp4",
      "stream-id": stream_id,
      "video-range": range,
    }
  }).then(response => response.blob())
  .then(blob => {
    const videoPlayer = document.getElementById("video");
    videoPlayer.src = URL.createObjectURL(blob);
    videoPlayer.play()
  });
}

function get_profile() {
  fetch(window.location.href+"profile", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    }
  }).then((response) => {    
    return response.json()
  }).then(data => {
    if (data.status) {
      dom_profile(data.userdata)
    } else {
      dom_logout()
    }
  })
}

function get_rtmp_data() {
  const status_div = document.getElementById("rtmp-status")
  ws_url = "ws://" + window.location.host + "/rtmp/status/ws"
  let ws = new WebSocket(ws_url)
  ws.onmessage = function(event) {
    let content = JSON.parse(event.data)
    if (content.error) {
      alert(content.error)
    } else if (content.message) {
      console.log(content.message)
    } else {
      status_div.innerHTML = ""
      for (const [key, value] of Object.entries(content)) {
        console.log(key, value)
        let p = document.createElement("p")
        p.classList="text-nowrap"
        p.style.margin=0
        p.innerText=`${key}: ${value}`
        status_div.append(p)
      }
    }
  }
}

function dom_stream_list(data) {
  const stream_list_elem = document.getElementById("stream-list")
  stream_list_elem.innerHTML = ""
  const stream_list = JSON.parse(data)
  stream_list.forEach(stream_object => {
    let li = document.createElement('li')
    li.classList='nav-item btn btn-outline-secondary'
    let span = document.createElement('span')
    span.classList.add('stream-item')
    span.classList.add('nav-link')
    span.classList.add('text-white')
    span.classList.add('d-flex')
    span.classList.add('justify-content-between')
    span.setAttribute('onclick', 'click_stream_list(this)')
    span.dataset.id = stream_object.stream_id
    span.innerText = stream_object.video_name
    li.appendChild(span)
    let svg = document.createElement('img')
    svg.src = "web/static/trash.svg"
    svg.setAttribute('stream_id', stream_object.stream_id)
    svg.setAttribute('video_name', stream_object.video_name)
    svg.setAttribute('data-bs-toggle', 'modal')
    svg.setAttribute('data-bs-target', '#confirmErase')
    svg.classList="trash btn btn-primary"
    svg.addEventListener('click',(event) => event.stopPropagation())
    svg.addEventListener('click', (event) => {
      let stream_id = event.target.attributes.stream_id.value
      let button = document.getElementById('erase')
      button.setAttribute('stream_id', stream_id)
      button.setAttribute('onclick', 'delete_stream(this)')
      document.getElementById('confirmBody').innerText = "Erasing " + event.target.attributes.video_name.value + "..."
    })
    span.appendChild(svg)
    stream_list_elem.appendChild(li)
  })
}

function dom_clip_list(response) {
  const clip_list_elem = document.getElementById("clip-list")
  clip_list_elem.innerHTML = ""
  const clip_list = JSON.parse(response)
  clip_list.forEach(stream_object => {
    let div = document.createElement('div')
    div.classList="clip-item"
    let li = document.createElement('li')
    li.classList='nav-item btn btn-outline-secondary col-12'
    li.id="item-"+stream_object['clip_id']
    let span = document.createElement('span')
    span.classList.add('clip-item')
    span.classList.add('nav-link')
    span.classList.add('text-white')
    span.classList.add('d-flex')
    span.classList.add('justify-content-between')
    span.setAttribute('onclick', 'click_clip_list(this)')
    span.setAttribute('data-bs-toggle', 'collapse')
    span.setAttribute('data-bs-target', '#clip-'+stream_object['clip_id'])
    span.setAttribute('aria-expanded', 'false')
    span.setAttribute('aria-controls', 'clip-'+stream_object['clip_id'])
    span.dataset.clip_id = stream_object['clip_id']
    span.dataset.stream_id = stream_object['stream_id']
    span.dataset.start_time = stream_object['start_time']
    span.dataset.end_time = stream_object['end_time']
    span.dataset.tag = stream_object['tag']
    span.innerText = stream_object['tag']
    li.appendChild(span)
    let svg = document.createElement('img')
    svg.src = "web/static/trash.svg"
    svg.setAttribute('clip_id', stream_object['clip_id'])
    svg.setAttribute('tag', stream_object['tag'])
    svg.setAttribute('data-bs-toggle', 'modal')
    svg.setAttribute('data-bs-target', '#confirmErase')
    svg.classList="trash btn btn-primary"
    svg.addEventListener('click',(event) => event.stopPropagation())
    svg.addEventListener('click', (event) => {
      let clip_id = event.target.attributes.clip_id.value
      let button = document.getElementById('erase')
      button.setAttribute('clip_id', clip_id)
      button.setAttribute('onclick', 'delete_clip(this)')
      document.getElementById('confirmBody').innerText = "Erasing " + event.target.attributes.tag.value + "..."
    })
    span.appendChild(svg)
    let accordion_div = document.createElement('div')
    accordion_div.classList="accordion-collapse collapse"
    accordion_div.id="clip-"+stream_object['clip_id']
    accordion_div.setAttribute('aria-labelledby', 'item-'+stream_object['clip_id'])
    /* input */
    let clip_div = dom_clip_detail(stream_object)
    div.appendChild(li)
    div.appendChild(clip_div)
    clip_list_elem.appendChild(div)
  })
}

function dom_clip_detail(stream_object) {
  let start = [Math.floor(stream_object['start_time'] / 3600).toString(), Math.floor((stream_object['start_time'] % 3600) / 60).toString(), (stream_object['start_time'] % 60).toString()]
  let end = [Math.floor(stream_object['end_time'] / 3600).toString(), Math.floor((stream_object['end_time'] % 3600) / 60).toString(), (stream_object['end_time'] % 60).toString()]
  let div = document.createElement('div')
  div.classList="accordion-collapse collapse accordion-body"
  div.dataset.clip_id = stream_object['clip_id']
  div.setAttribute("data-bs-parent", "#clip-list")
  div.id="clip-"+stream_object['clip_id']
  let tag_h6 = document.createElement('h6')
  tag_h6.innerText = "Clip Tag"
  div.appendChild(tag_h6)

  let tag_div = document.createElement('div')
  tag_div.classList="tag-input"
  let tag_input = document.createElement('input')
  tag_input.name='tag'
  tag_input.dataset.tag = stream_object['tag']
  tag_input.value = stream_object['tag']
  tag_div.appendChild(tag_input)
  div.appendChild(tag_div)

  let time_h6 = document.createElement('h6')
  time_h6.innerText = "Clip Timestamp"
  div.appendChild(time_h6)

  let time_div = document.createElement('div')
  time_div.classList="time-input"
  time_div.dataset.stream_id = stream_object['stream_id']
  time_div.dataset.start_time = stream_object['start_time']
  time_div.dataset.end_time = stream_object['end_time']
  let img = document.createElement('img')
  img.src="web/static/clock.svg"
  img.alt="#"

  let colon = document.createElement('span')
  colon.innerText=":"
  let dash = document.createElement('span')
  dash.style.margin="0 5px 0 5px"
  dash.innerText="-"
  let s_hour = document.createElement('input')
  s_hour.name="s-hour"
  s_hour.placeholder="00"
  s_hour.value=start[0]
  let s_minute = document.createElement('input')
  s_minute.name="s-minute"
  s_minute.placeholder="00"
  s_minute.value=start[1]
  let s_second = document.createElement('input')
  s_second.name="s-second"
  s_second.placeholder="00"
  s_second.value=start[2]
  let e_hour = document.createElement('input')
  e_hour.name="e-hour"
  e_hour.placeholder="00"
  e_hour.value=end[0]
  let e_minute = document.createElement('input')
  e_minute.name="e-minute"
  e_minute.placeholder="00"
  e_minute.value=end[1]
  let e_second = document.createElement('input')
  e_second.name="e-second"
  e_second.placeholder="00"
  e_second.value=end[2]

  time_div.appendChild(img.cloneNode(true))
  time_div.appendChild(s_hour)
  time_div.appendChild(colon.cloneNode(true))
  time_div.appendChild(s_minute)
  time_div.appendChild(colon.cloneNode(true))
  time_div.appendChild(s_second)
  time_div.appendChild(dash)
  time_div.appendChild(img.cloneNode(true))
  time_div.appendChild(e_hour)
  time_div.appendChild(colon.cloneNode(true))
  time_div.appendChild(e_minute)
  time_div.appendChild(colon.cloneNode(true))
  time_div.appendChild(e_second)
  time_div.addEventListener('focusout', (event) => {
    if (event.relatedTarget==null) {
      focusout_input()
    }
  })
  div.appendChild(time_div)

  let submit_btn = document.createElement('button')
  submit_btn.type="button"
  submit_btn.classList="btn btn-primary submit"
  submit_btn.innerText="Submit"
  submit_btn.setAttribute("onclick", "clip_submit()")
  div.appendChild(submit_btn)

  return div
}

function dom_profile(profile) {
  const profile_elem = document.getElementById('profile')
  profile_elem.innerHTML=''
  const a = document.createElement('a')
  a.classList='btn d-flex align-items-center text-white text-decoration-none dropdown-toggle'
  a.setAttribute('data-bs-toggle', 'dropdown');
  const profile_image = document.createElement('img')
  profile_image.classList='rounded-circle me-2'
  profile_image.id='profile_image'
  profile_image.width=32
  profile_image.height=32
  profile_image.src = profile['profile_image_url']
  a.appendChild(profile_image)
  const strong = document.createElement('strong')
  strong.innerText = profile['display_name']
  a.appendChild(strong)
  const ul = document.createElement('ul')
  ul.classList='dropdown-menu dropdown-menu-dark text-small shadow'
  const li_setting = document.createElement('li')
  const a_setting = document.createElement('a')
  a_setting.classList='dropdown-item'
  a_setting.setAttribute('data-bs-toggle', 'modal')
  a_setting.setAttribute('data-bs-target', '#setting')
  a_setting.setAttribute('onclick', 'get_config_data()')
  a_setting.innerText='Setting'
  li_setting.appendChild(a_setting)
  const li_div = document.createElement('li')
  const hr = document.createElement('hr')
  hr.classList='dropdown-divider'
  li_div.appendChild(hr)
  const li_logout = document.createElement('li')
  const a_logout = document.createElement('a')
  a_logout.classList='dropdown-item'
  a_logout.href='/logout'
  a_logout.innerText='Logout'
  li_logout.appendChild(a_logout)
  ul.appendChild(li_setting)
  ul.appendChild(li_div)
  ul.appendChild(li_logout)
  profile_elem.appendChild(a)
  profile_elem.appendChild(ul)
}

function dom_form(data) {
  Object.keys(data).forEach(key => {
    let element = document.querySelector("input[name="+key.replaceAll('_','-')+"]")
    if (element.type=="checkbox") {
      if ((element.checked & data[key]=='False') || (!element.checked & data[key]=='True')){
        element.click()
      }
    } else {
      element.value=data[key]
    }
  })
}

function dom_logout() {
  const profile_elem = document.getElementById('profile')
  profile_elem.innerHTML=''
  const a = document.createElement('a')
  a.classList = 'btn btn-primary col-12'
  a.innerText = 'Login Twitch'
  a.setAttribute('href', window.location.href + 'login')
  profile_elem.appendChild(a)
}

function click_stream_list(element) {
  const before_element = document.getElementsByClassName('stream-item nav-link active')
  Array.prototype.forEach.call(before_element, (e)=> {
    e.classList.remove('active');
    e.classList.add('text-white');
  });
  element.classList.add('active');
  get_clip_data(element.dataset.id);
}

function click_clip_list(element) {
  if (!element.classList.contains('active')) {
    const before_element = document.getElementsByClassName('clip-item nav-link active')
    Array.prototype.forEach.call(before_element, (e) => {
      e.classList.remove('active');
      e.classList.add('text-white');
    });
    element.classList.add('active');
    get_video_data(element.dataset.stream_id, element.dataset.start_time, element.dataset.end_time);
  }
} 

function focusout_input() {
  let accordion = document.getElementsByClassName("accordion-collapse show")[0]
  let time_div = accordion.getElementsByClassName("time-input")[0]
  let stream_id = time_div.dataset.stream_id
  let s_hour = parseInt(time_div.children['s-hour'].value | 0)
  let s_minute = parseInt(time_div.children['s-minute'].value | 0)
  let s_second = parseInt(time_div.children['s-second'].value | 0)
  let e_hour = parseInt(time_div.children['e-hour'].value | 0)
  let e_minute = parseInt(time_div.children['e-minute'].value | 0)
  let e_second = parseInt(time_div.children['e-second'].value | 0)
  let start = s_hour*3600+s_minute*60+s_second
  let end = e_hour*3600+e_minute*60+e_second
  if (start>end){
    alert("Invalid TimeDelta.")
  } else if (end-start>120) {
    alert("TimeDelta is too Large.")
  } else if (start==element.dataset.start_time && end==element.dataset.end_time) {
    return
  } else {
    get_video_data(stream_id, start, end)
  }
}

function clip_submit() {
  let accordion = document.getElementsByClassName("accordion-collapse show")[0]
  let tag_div = accordion.getElementsByClassName("tag-input")[0]
  let tag = tag_div.children['tag'].value
  let time_div = accordion.getElementsByClassName("time-input")[0]
  let s_hour = parseInt(time_div.children['s-hour'].value | 0)
  let s_minute = parseInt(time_div.children['s-minute'].value | 0)
  let s_second = parseInt(time_div.children['s-second'].value | 0)
  let e_hour = parseInt(time_div.children['e-hour'].value | 0)
  let e_minute = parseInt(time_div.children['e-minute'].value | 0)
  let e_second = parseInt(time_div.children['e-second'].value | 0)
  let start = s_hour*3600+s_minute*60+s_second
  let end = e_hour*3600+e_minute*60+e_second
  if (start>end){
    alert("Invalid TimeDelta.")
  } else if (end-start>120) {
    alert("TimeDelta is too Large.")
  } else if (tag==tag_div.dataset.tag && start==time_div.dataset.start_time && end==time_div.dataset.end_time) {
    return
  } else {
    console.log([accordion.dataset.clip_id, start, end, 'null', tag, 'null'])
    let url = window.location.href + "db/edit"
    fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        "table" : "tb_clip_time",
        "row" : [accordion.dataset.clip_id, start, end, 'null', tag, 'null']
      })
    }).then((response) => {
      if (!response.ok) {
        return response.json()
      }
    }).then(error_data => {
      if (error_data) {
        alert(error_data.detail)
      }
    })
  }
}

function click_server_start() {
  const url = window.location.href+"rtmp/start"
  fetch(url, {
    method: "GET"
  }).then(response => {
    if (!response.ok) {
      return response.json()
    }
  }).then(error_data => {
    if (error_data) {
      alert(error_data.detail)
    } else {
      document.getElementById("rtmp-status").classList="Collapse.show"
      const button = document.getElementById("rtmp-switch")
      button.setAttribute("onclick", "click_server_end()")
      button.innerText="Server Stop"
      get_rtmp_data()
    }
  })
}

function click_server_end(){
  const url = window.location.href+"rtmp/end"
  fetch(url, {
    method: "GET"
  }).then(response => {
    if (!response.ok) {
      return response.json()
    }
  }).then(error_data => {
    if (error_data) {
      alert(error_data.detail)
    } else {
      document.getElementById("rtmp-status").classList="d-none"
      const button = document.getElementById("rtmp-switch")
      button.setAttribute("onclick", "click_server_start()")
      button.innerText="Server Start"
    }
  })
}

function submit_config(){
  const url = window.location.href+"conf/set"
  document.querySelectorAll("form p").forEach(element => {element.hidden=true})

  const confData = new Object();
  document.querySelectorAll("form .modal-body input").forEach(element => {
    if (element.type=='checkbox'){
      confData[element.name.replaceAll('-','_')]=element.checked;
    } else {
      confData[element.name.replaceAll('-','_')]=element.value;
    }
  })

  let message = null
  if (confData['start_time_interval']>confData['end_time_interval']) {
    message = "Start time is bigger than end time."
  } else if (confData['start_time_interval']>0 || confData['end_time_interval']<0) {
    message = "Set the time interval to include Clip timestamps(0s)."
  } else if (confData['end_time_interval']-confData['start_time_interval']>120){
    message = "Time interval is too long(over 120s)."
  }
  if (message) {
    let element = document.querySelector("#time-interval-message")
    element.hidden=false
    element.innerText = message
    return null
  }
  
  fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(confData)
  }).then(response => {
    if (!response.ok) {
      alert(response.detail)
    } else {
      return response.json()
    }
  }).then(data => {
    if (data['isValid']) {
      alert("Save Success.")
    } else {
      let element = document.querySelector("#" + data['invalidData'].replaceAll("_","-")+"-message")
      element.hidden=false
      element.innerText = data['detail']
    }
  })
}

function delete_stream(element){
  const url = window.location.href+"db/delete/stream/"+element.attributes.stream_id.value
  fetch(url, {
    method: "GET"
  }).then(response => {
    if (!response.ok) {
      alert(response.json())
    } else {
      get_stream_data()
    }
  })
}

function delete_clip(element){
  const url = window.location.href+"db/delete/clip/"+element.attributes.clip_id.value
  console.log(url)
  fetch(url, {
    method: "GET"
  }).then(response => {
    if (!response.ok) {
      alert(response.json())
    } else {
      let stream_id = document.getElementsByClassName("stream-item nav-link active")[0].dataset.id
      get_clip_data(stream_id)
    }
  })
}

function main(){
  //get current status
  get_profile()
  get_config_data()
  fetch (window.location.href+"rtmp/status", {
    method: "GET"
  }).then(response => {
    if (response.ok) {
      return response.json()
    }
  }).then(data => {
    if (data['isRunning']) {
      document.getElementById("rtmp-status").classList=""
      const button = document.getElementById("rtmp-switch")
      button.setAttribute("onclick", "click_server_end()")
      button.innerText="Server Stop"
      get_rtmp_data()
    }
  })
  get_stream_data()
}

window.addEventListener("load", main)