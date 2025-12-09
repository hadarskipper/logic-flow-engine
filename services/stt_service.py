"""Mock Speech-to-Text service."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def transcribe_audio(audio_file: Any) -> str:
    """
    Mock STT function that returns sample transcribed text.
    
    Args:
        audio_file: Audio file object (not actually processed in mock)
        
    Returns:
        Sample transcribed text string
    """
    logger.info("Mock STT: Transcribing audio file")
    
    # Mock transcription - in real implementation, this would process the audio
    moch_transcription_options = [
        """
        Hospital → Patient
Hospital: Lakeshore Community Health Center

Nurse: Hello, this is Emma from Lakeshore Community Health Center. Am I speaking with Mr. Jonathan Hale?

Patient: Yeah, that’s me.

Nurse: I’m calling to check in regarding your recent visit for persistent migraines. How have you been since then?

Patient: The migraines come and go. But honestly… that’s not the main thing right now.

Nurse: Okay. I understand. What’s been going on?

Patient: I’ve just been overwhelmed. Work is a mess, I’m taking care of my mom after her surgery, and the headaches always hit on the worst days. I know this isn’t really medical, but… I don’t really have anyone to talk to.

Nurse: It sounds like you've been under a lot of pressure, Jonathan.

Patient: Yeah. It’s been months of this. Feels like everything’s just piling up. I’m exhausted.

Nurse: Thank you for telling me that. Just so you're aware, I need to stay within the medical scope of this call—I can’t discuss non-health personal issues in detail—but I can focus on anything that affects your treatment or symptoms.
So let’s look at what could be medically relevant. Over the last week, have your migraines changed in frequency or intensity?

Patient: No, they’ve been about the same. Still the same pulsing pain behind the eyes.

Nurse: Okay. Any new symptoms—vision changes, nausea, sensitivity to light that's worse than before?

Patient: No, nothing like that.

Nurse: Alright. I’ll update your chart and have the physician review whether we should adjust your treatment plan. If you ever experience a sudden change in headache severity, neurological symptoms, or anything unusual, please contact us immediately.

Patient: Okay… yeah. Thanks.

Nurse: And Jonathan—just to reiterate, I can’t engage with the non-medical pressures you mentioned, but I hear that things are difficult. If you think it would be helpful, I can connect you with our behavioral health team—they deal with stress management and coping strategies that directly relate to health.

Patient: Maybe later. For now I just needed to say something out loud.

Nurse: Understood. Is there anything else medically related that I can help you with today?

Patient: No, that’s it.

Nurse: Alright. I’ll send you a message once the doctor reviews your migraine management plan. Take care, Jonathan.
        """,
        """
        Patient → Hospital
Hospital: Greenfield Internal Medicine

Receptionist: Greenfield Internal Medicine, this is Tom. How can I assist you today?

Patient: Hi, this is Yael Mizrahi. I need a refill for my blood-pressure medication, Amlodipine, but the pharmacy says the prescription expired.

Receptionist: I can help with that. When was your last appointment with us?

Patient: About six months ago.

Receptionist: Okay. You’re still within the refill window, so I’ll send a renewal request to the physician. Which pharmacy should we send it to?

Patient: The same one—SuperPharm in Herzliya.

Receptionist: Noted. The refill should be ready later today. While we’re at it, any side effects or issues with the medication?

Patient: No, it’s been fine.

Receptionist: Great. We’ll text you once the doctor approves the renewal. Anything else today?

Patient: No, that’s it. Thanks.
        """,
        """
        Patient → Hospital
Hospital: North Hill Urgent Care

Receptionist: North Hill Urgent Care, this is Dana. How can I help you?

Patient: Hi, this is Amir Levi. I’m feeling unwell—fever, chills, and a strong cough since last night. I wanted to know if I should come in.

Receptionist: Sorry to hear that. Let me ask a few quick questions. What’s your current temperature?

Patient: About 38.6°C.

Receptionist: Any shortness of breath or chest pain?

Patient: No chest pain. Breathing is okay, just the coughing.

Receptionist: Understood. Any recent COVID or flu exposure?

Patient: My daughter had the flu this week.

Receptionist: Based on your symptoms, we recommend you come in for evaluation and a flu test today. Earliest walk-in availability is in about 45 minutes. Do you need instructions for the clinic?

Patient: No, I know where it is. I’ll come in.

Receptionist: Great. Bring your ID and insurance card. If at any point you develop difficulty breathing, go to the emergency department immediately.

Patient: Will do. Thanks.
        """,
        """
        Hospital → Patient
Hospital: Riverside Family Clinic

Coordinator: Hello, may I speak with Maya Ben-Shahar?

Patient: Speaking.

Coordinator: Hi Maya, this is Lior from Riverside Family Clinic. We’re reaching out because you’re due for your annual wellness exam. Would you like to schedule it?

Patient: Sure. What’s available?

Coordinator: We have openings next Wednesday at 14:00 or Thursday morning at 9:30.

Patient: Wednesday at 14:00 works.

Coordinator: Booked. Before the appointment, please fast for 8 hours so we can run your routine blood tests. Any chronic medications you’ve changed since last year?

Patient: I started a new thyroid medication two months ago.

Coordinator: Got it—I’ll note it for the doctor. Anything else you want checked?

Patient: Maybe Vitamin D levels.

Coordinator: Added. You’ll get an SMS reminder 24 hours before. Thanks and have a great day.
        """,
        """
        Hospital → Patient
Hospital: Cityview Medical Center

Nurse: Hi, this is Sarah calling from Cityview Medical Center. Am I speaking with David Cohen?

Patient: Yes, this is David.

Nurse: Great. I’m calling to follow up on your discharge from the hospital yesterday after your appendectomy. How are you feeling today?

Patient: Sore, but mostly okay.

Nurse: That’s normal for day one. Any fever, increased pain, redness around the incision, or trouble keeping food down?

Patient: No fever. Pain is manageable. The incision looks fine.

Nurse: Good. Are you taking the prescribed antibiotics and pain meds as instructed?

Patient: Yes, exactly as written.

Nurse: Excellent. Your follow-up appointment is scheduled for next Tuesday at 10 AM. Do you need help arranging transportation?

Patient: No, I’m covered.

Nurse: Perfect. If any symptoms worsen—fever above 38°C, severe abdominal pain, or discharge from the incision—call us immediately. Anything else I can help with?

Patient: No, that’s all. Thanks.
        """
    ]
    return random.choice(moch_transcription_options)

