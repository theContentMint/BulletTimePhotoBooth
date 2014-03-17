

int x;
boolean person;

void setup()
{
  Serial.begin(9600);
  pinMode(13, OUTPUT); 
}

void loop()
{
  x = analogRead(0);
  
  if (x<400) {
    person = true;
    
    Serial.println('T');
    digitalWrite(13,HIGH);
    
    while (person) {
      x = analogRead(0);
      if (x>600) {
        person = false;
        digitalWrite(13,LOW);
      }
      delay(50);
    }
    
  }
  delay(50);
}
