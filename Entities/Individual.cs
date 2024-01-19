using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ExxerciseAbstractMethods.Entities
{
    class Individual : TaxPayer
    {
        public double HealthExpenditures { get; set; }

        public Individual() { }

        public Individual(string name, double anualIncome ,double healthExpenditures) : base(name, anualIncome)
        {
            HealthExpenditures = healthExpenditures;
        }

        public override double Tax()
        {
            double tax = 0;
            if (AnualIncome < 20000.00)
            {
                tax = AnualIncome * 0.15;
                if(HealthExpenditures > 0)
                {
                    tax = tax - HealthExpenditures * 0.5;
                }
            }
            else if (AnualIncome > 20000.00)
            {
                tax = AnualIncome * 0.25;
                if(HealthExpenditures > 0)
                {
                    tax = tax - HealthExpenditures * 0.5;
                }
            }

            return tax;
        }
    }
}
