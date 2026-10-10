/**
 * Daily Life Pets and Companion Animals Registry
 * Supports dogs, cats, birds, rabbits, hamsters, fish, turtles, reptiles, horses, cows, goats, pigs, ferrets, etc.
 */

export const DAILY_LIFE_SPECIES = [
  { value: 'Dog', label: '🐶 Dog (Canine)', emoji: '🐶' },
  { value: 'Cat', label: '🐱 Cat (Feline)', emoji: '🐱' },
  { value: 'Bird', label: '🦜 Bird / Parrot / Avian', emoji: '🦜' },
  { value: 'Rabbit', label: '🐰 Rabbit / Bunny', emoji: '🐰' },
  { value: 'Hamster', label: '🐹 Hamster / Guinea Pig / Rodent', emoji: '🐹' },
  { value: 'Fish', label: '🐠 Fish / Aquarium Pet', emoji: '🐠' },
  { value: 'Turtle', label: '🐢 Turtle / Tortoise', emoji: '🐢' },
  { value: 'Reptile', label: '🦎 Reptile (Gecko, Lizard, Bearded Dragon)', emoji: '🦎' },
  { value: 'Horse', label: '🐎 Horse / Pony / Equine', emoji: '🐎' },
  { value: 'Cow', label: '🐄 Cow / Cattle / Calf', emoji: '🐄' },
  { value: 'Goat', label: '🐐 Goat / Sheep', emoji: '🐐' },
  { value: 'Pig', label: '🐖 Pig / Mini Pot-Bellied Pig', emoji: '🐖' },
  { value: 'Ferret', label: '🐾 Ferret', emoji: '🐾' },
  { value: 'Other', label: '✨ Other Daily Life Pet (Custom)', emoji: '🐾' },
];

export const getSpeciesEmoji = (species = '') => {
  if (!species) return '🐾';
  const s = String(species).toLowerCase();
  if (s.includes('cat') || s.includes('feline')) return '🐱';
  if (s.includes('dog') || s.includes('canine')) return '🐶';
  if (s.includes('bird') || s.includes('parrot') || s.includes('avian') || s.includes('cockatiel') || s.includes('budgie') || s.includes('finch') || s.includes('pigeon') || s.includes('canary')) return '🦜';
  if (s.includes('rabbit') || s.includes('bunny') || s.includes('hare')) return '🐰';
  if (s.includes('hamster') || s.includes('guinea') || s.includes('gerbil') || s.includes('rodent') || s.includes('mouse') || s.includes('rat') || s.includes('chinchilla')) return '🐹';
  if (s.includes('fish') || s.includes('aquatic') || s.includes('goldfish') || s.includes('betta')) return '🐠';
  if (s.includes('turtle') || s.includes('tortoise')) return '🐢';
  if (s.includes('reptile') || s.includes('lizard') || s.includes('gecko') || s.includes('snake') || s.includes('dragon')) return '🦎';
  if (s.includes('horse') || s.includes('pony') || s.includes('equine') || s.includes('donkey')) return '🐎';
  if (s.includes('cow') || s.includes('cattle') || s.includes('calf') || s.includes('bovine')) return '🐄';
  if (s.includes('goat') || s.includes('sheep') || s.includes('lamb')) return '🐐';
  if (s.includes('pig') || s.includes('swine') || s.includes('hog')) return '🐖';
  if (s.includes('ferret')) return '🐾';
  return '🐾';
};
